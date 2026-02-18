"""
Batch Import Tool - 批量导入工具

功能:
1. 文件夹批量上传（支持递归子目录）
2. PDF/URL 列表导入
3. Zotero/Mendeley 导出文件解析
4. 自动去重和验证
5. 进度追踪和错误处理
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from xml.etree import ElementTree as ET

from loguru import logger

from open_notebook.domain.notebook import Notebook, Source


class BatchImporter:
    """批量导入器"""
    
    def __init__(self, notebook_id: str):
        self.notebook_id = notebook_id
        self.notebook: Optional[Notebook] = None
        
    async def initialize(self):
        """初始化"""
        logger.info(f"Initializing BatchImporter for notebook {self.notebook_id}")
        self.notebook = await Notebook.get(self.notebook_id)
        if not self.notebook:
            raise ValueError(f"Notebook {self.notebook_id} not found")
    
    async def import_from_folder(
        self,
        folder_path: str,
        recursive: bool = True,
        supported_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """从文件夹批量导入
        
        Args:
            folder_path: 文件夹路径
            recursive: 是否递归子目录
            supported_extensions: 支持的扩展名
            
        Returns:
            导入结果统计
        """
        if supported_extensions is None:
            supported_extensions = ['.pdf', '.docx', '.pptx', '.xlsx', '.txt', '.md']
        
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # 收集所有文件
        files_to_import = []
        if recursive:
            for ext in supported_extensions:
                files_to_import.extend(folder.rglob(f"*{ext}"))
        else:
            for ext in supported_extensions:
                files_to_import.extend(folder.glob(f"*{ext}"))
        
        logger.info(f"Found {len(files_to_import)} files to import")
        
        # 导入文件
        results = {
            'total_found': len(files_to_import),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        for i, file_path in enumerate(files_to_import, 1):
            try:
                logger.info(f"[{i}/{len(files_to_import)}] Importing: {file_path.name}")
                
                # 检查是否已存在（基于文件名）
                if await self._is_duplicate(file_path.name):
                    logger.warning(f"Duplicate detected: {file_path.name}, skipping...")
                    results['skipped'] += 1
                    continue
                
                # 创建 Source
                source = Source(
                    title=file_path.stem,
                    asset={
                        'type': 'file',
                        'file_path': str(file_path.absolute()),
                        'mime_type': self._get_mime_type(file_path.suffix)
                    }
                )
                await source.save()
                await source.add_to_notebook(self.notebook_id)
                
                # 触发异步处理
                asyncio.create_task(source.process())
                
                results['successful'] += 1
                
            except Exception as e:
                logger.error(f"Failed to import {file_path.name}: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'file': str(file_path),
                    'error': str(e)
                })
        
        return results
    
    async def import_urls(
        self,
        urls: List[str],
        validate_first: bool = True
    ) -> Dict[str, Any]:
        """批量导入 URL
        
        Args:
            urls: URL 列表
            validate_first: 是否先验证 URL 可访问性
            
        Returns:
            导入结果统计
        """
        logger.info(f"Importing {len(urls)} URLs")
        
        results = {
            'total': len(urls),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for i, url in enumerate(urls, 1):
            try:
                logger.info(f"[{i}/{len(urls)}] Importing: {url}")
                
                # 简单验证
                if validate_first and not url.startswith(('http://', 'https://')):
                    raise ValueError(f"Invalid URL format: {url}")
                
                # 检查重复
                if await self._is_duplicate(url):
                    logger.warning(f"Duplicate URL detected: {url}, skipping...")
                    results['successful'] += 1  # 已存在也算成功
                    continue
                
                # 创建 Source
                source = Source(
                    title=url.split('/')[-1][:100],  # 简化标题
                    asset={
                        'type': 'url',
                        'url': url
                    }
                )
                await source.save()
                await source.add_to_notebook(self.notebook_id)
                
                # 触发异步处理
                asyncio.create_task(source.process())
                
                results['successful'] += 1
                
            except Exception as e:
                logger.error(f"Failed to import {url}: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'url': url,
                    'error': str(e)
                })
        
        return results
    
    async def import_zotero_export(
        self,
        export_file: str
    ) -> Dict[str, Any]:
        """导入 Zotero 导出的 RIS/BibTeX 文件
        
        Args:
            export_file: Zotero 导出文件路径
            
        Returns:
            导入结果统计
        """
        file_path = Path(export_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Export file not found: {export_file}")
        
        logger.info(f"Importing Zotero export: {export_file}")
        
        results = {
            'total_entries': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # 根据文件类型选择解析器
        if file_path.suffix.lower() == '.ris':
            entries = self._parse_ris(file_path)
        elif file_path.suffix.lower() in ['.bib', '.bibtex']:
            entries = self._parse_bibtex(file_path)
        elif file_path.suffix.lower() == '.xml':
            entries = self._parse_zotero_xml(file_path)
        else:
            raise ValueError(f"Unsupported export format: {file_path.suffix}")
        
        results['total_entries'] = len(entries)
        
        # 导入每个条目
        for i, entry in enumerate(entries, 1):
            try:
                logger.info(f"[{i}/{len(entries)}] Importing Zotero entry: {entry.get('title', 'Untitled')}")
                
                # 检查重复（基于标题或 DOI）
                identifier = entry.get('doi') or entry.get('title')
                if identifier and await self._is_duplicate(identifier):
                    logger.warning(f"Duplicate entry detected: {identifier}, skipping...")
                    results['successful'] += 1
                    continue
                
                # 创建 Source
                source_data = {
                    'title': entry.get('title', 'Untitled'),
                    'topics': entry.get('keywords', []),
                    'asset': {}
                }
                
                # 添加 URL 如果有
                if 'url' in entry:
                    source_data['asset']['type'] = 'url'
                    source_data['asset']['url'] = entry['url']
                
                # 添加文件路径如果有
                if 'file_path' in entry:
                    source_data['asset']['type'] = 'file'
                    source_data['asset']['file_path'] = entry['file_path']
                
                source = Source(**source_data)
                await source.save()
                await source.add_to_notebook(self.notebook_id)
                
                # 触发异步处理
                asyncio.create_task(source.process())
                
                results['successful'] += 1
                
            except Exception as e:
                logger.error(f"Failed to import Zotero entry: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'entry': entry.get('title', 'Untitled'),
                    'error': str(e)
                })
        
        return results
    
    async def import_mendeley_export(
        self,
        export_file: str
    ) -> Dict[str, Any]:
        """导入 Mendeley 导出的 CSV/XML 文件
        
        Args:
            export_file: Mendeley 导出文件路径
            
        Returns:
            导入结果统计
        """
        file_path = Path(export_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Export file not found: {export_file}")
        
        logger.info(f"Importing Mendeley export: {export_file}")
        
        results = {
            'total_entries': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Mendeley 通常导出 CSV 或 XML
        if file_path.suffix.lower() == '.csv':
            entries = self._parse_csv(file_path)
        elif file_path.suffix.lower() == '.xml':
            entries = self._parse_mendeley_xml(file_path)
        else:
            raise ValueError(f"Unsupported Mendeley export format: {file_path.suffix}")
        
        results['total_entries'] = len(entries)
        
        # 导入逻辑与 Zotero 类似
        for i, entry in enumerate(entries, 1):
            try:
                logger.info(f"[{i}/{len(entries)}] Importing Mendeley entry: {entry.get('title', 'Untitled')}")
                
                # 检查重复
                identifier = entry.get('doi') or entry.get('title')
                if identifier and await self._is_duplicate(identifier):
                    logger.warning(f"Duplicate entry detected: {identifier}, skipping...")
                    results['successful'] += 1
                    continue
                
                # 创建 Source
                source_data = {
                    'title': entry.get('title', 'Untitled'),
                    'topics': entry.get('keywords', []),
                    'asset': {}
                }
                
                if 'url' in entry:
                    source_data['asset']['type'] = 'url'
                    source_data['asset']['url'] = entry['url']
                
                if 'file_path' in entry:
                    source_data['asset']['type'] = 'file'
                    source_data['asset']['file_path'] = entry['file_path']
                
                source = Source(**source_data)
                await source.save()
                await source.add_to_notebook(self.notebook_id)
                
                asyncio.create_task(source.process())
                results['successful'] += 1
                
            except Exception as e:
                logger.error(f"Failed to import Mendeley entry: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'entry': entry.get('title', 'Untitled'),
                    'error': str(e)
                })
        
        return results
    
    async def import_pdf_list_with_metadata(
        self,
        pdf_folder: str,
        metadata_file: str
    ) -> Dict[str, Any]:
        """批量导入 PDF 并附带元数据
        
        Args:
            pdf_folder: PDF 文件所在文件夹
            metadata_file: 元数据 JSON 文件路径
            
        Returns:
            导入结果统计
        """
        metadata_path = Path(metadata_file)
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata_list = json.load(f)
        
        logger.info(f"Importing {len(metadata_list)} PDFs with metadata")
        
        results = {
            'total': len(metadata_list),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for i, meta in enumerate(metadata_list, 1):
            try:
                pdf_filename = meta.get('filename')
                if not pdf_filename:
                    raise ValueError("Missing filename in metadata")
                
                pdf_path = Path(pdf_folder) / pdf_filename
                if not pdf_path.exists():
                    raise FileNotFoundError(f"PDF not found: {pdf_path}")
                
                logger.info(f"[{i}/{len(metadata_list)}] Importing: {pdf_filename}")
                
                # 检查重复
                if await self._is_duplicate(pdf_filename):
                    logger.warning(f"Duplicate PDF detected: {pdf_filename}, skipping...")
                    results['successful'] += 1
                    continue
                
                # 创建 Source
                source = Source(
                    title=meta.get('title', pdf_filename.stem),
                    topics=meta.get('keywords', []),
                    asset={
                        'type': 'file',
                        'file_path': str(pdf_path.absolute()),
                        'mime_type': 'application/pdf'
                    }
                )
                await source.save()
                await source.add_to_notebook(self.notebook_id)
                
                asyncio.create_task(source.process())
                results['successful'] += 1
                
            except Exception as e:
                logger.error(f"Failed to import PDF: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'pdf': meta.get('filename', 'Unknown'),
                    'error': str(e)
                })
        
        return results
    
    def _parse_ris(self, file_path: Path) -> List[Dict[str, Any]]:
        """解析 RIS 格式"""
        entries = []
        current_entry = {}
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('TY  -'):
                    if current_entry:
                        entries.append(current_entry)
                    current_entry = {'type': line.split('  - ')[1]}
                elif line.startswith('ER  -'):
                    if current_entry:
                        entries.append(current_entry)
                        current_entry = {}
                elif '  - ' in line:
                    tag, value = line.split('  - ', 1)
                    if tag == 'TI':
                        current_entry['title'] = value
                    elif tag == 'KW':
                        if 'keywords' not in current_entry:
                            current_entry['keywords'] = []
                        current_entry['keywords'].append(value)
                    elif tag == 'UR':
                        current_entry['url'] = value
                    elif tag == 'DO':
                        current_entry['doi'] = value
        
        if current_entry and 'type' in current_entry:
            entries.append(current_entry)
        
        return entries
    
    def _parse_bibtex(self, file_path: Path) -> List[Dict[str, Any]]:
        """解析 BibTeX 格式（简化版）"""
        entries = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 简单的正则匹配（完整版需要更复杂的解析）
        import re
        pattern = r'@(\w+)\{([^,]+),\s*(.*?)\}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            entry_type, cite_key, fields_str = match
            entry = {'type': entry_type, 'cite_key': cite_key}
            
            # 解析字段
            field_pattern = r'(\w+)\s*=\s*\{([^}]*)\}'
            fields = re.findall(field_pattern, fields_str)
            for field_name, field_value in fields:
                if field_name == 'title':
                    entry['title'] = field_value
                elif field_name == 'keywords':
                    entry['keywords'] = [k.strip() for k in field_value.split(',')]
                elif field_name == 'url':
                    entry['url'] = field_value
                elif field_name == 'doi':
                    entry['doi'] = field_value
            
            entries.append(entry)
        
        return entries
    
    def _parse_zotero_xml(self, file_path: Path) -> List[Dict[str, Any]]:
        """解析 Zotero XML 格式"""
        entries = []
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for item in root.findall('.//item'):
            entry = {}
            
            title_elem = item.find(".//field[@name='title']")
            if title_elem is not None and title_elem.get('value'):
                entry['title'] = title_elem.get('value')
            
            tags_elem = item.findall(".//tag")
            if tags_elem:
                entry['keywords'] = [tag.get('tag') for tag in tags_elem]
            
            url_elem = item.find(".//field[@name='url']")
            if url_elem is not None and url_elem.get('value'):
                entry['url'] = url_elem.get('value')
            
            doi_elem = item.find(".//field[@name='DOI']")
            if doi_elem is not None and doi_elem.get('value'):
                entry['doi'] = doi_elem.get('value')
            
            entries.append(entry)
        
        return entries
    
    def _parse_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """解析 CSV 格式"""
        import csv
        
        entries = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = {}
                if 'Title' in row:
                    entry['title'] = row['Title']
                if 'Keywords' in row:
                    entry['keywords'] = [k.strip() for k in row['Keywords'].split(';')]
                if 'Url' in row:
                    entry['url'] = row['Url']
                if 'DOI' in row:
                    entry['doi'] = row['DOI']
                entries.append(entry)
        
        return entries
    
    def _parse_mendeley_xml(self, file_path: Path) -> List[Dict[str, Any]]:
        """解析 Mendeley XML 格式"""
        entries = []
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for doc in root.findall('.//document'):
            entry = {}
            
            title_elem = doc.find('title')
            if title_elem is not None and title_elem.text:
                entry['title'] = title_elem.text
            
            keywords_elem = doc.find('keywords')
            if keywords_elem is not None:
                entry['keywords'] = [kw.text for kw in keywords_elem.findall('keyword')]
            
            url_elem = doc.find('website')
            if url_elem is not None and url_elem.text:
                entry['url'] = url_elem.text
            
            doi_elem = doc.find('doi')
            if doi_elem is not None and doi_elem.text:
                entry['doi'] = doi_elem.text
            
            entries.append(entry)
        
        return entries
    
    async def _is_duplicate(self, identifier: str) -> bool:
        """检查是否重复"""
        # TODO: 实际实现需要查询数据库
        # 当前版本简化处理：总是返回 False
        return False
    
    def _get_mime_type(self, extension: str) -> str:
        """获取 MIME 类型"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.txt': 'text/plain',
            '.md': 'text/markdown'
        }
        return mime_types.get(extension.lower(), 'application/octet-stream')
    
    async def close(self):
        """关闭"""
        logger.info("Closing BatchImporter")


# ============================================================================
# Convenience Functions
# ============================================================================

async def batch_import_files(notebook_id: str, folder_path: str, recursive: bool = True) -> Dict[str, Any]:
    """便捷函数：批量导入文件"""
    importer = BatchImporter(notebook_id)
    await importer.initialize()
    try:
        return await importer.import_from_folder(folder_path, recursive)
    finally:
        await importer.close()


async def batch_import_urls(notebook_id: str, urls: List[str]) -> Dict[str, Any]:
    """便捷函数：批量导入 URL"""
    importer = BatchImporter(notebook_id)
    await importer.initialize()
    try:
        return await importer.import_urls(urls)
    finally:
        await importer.close()


async def import_zotero_library(notebook_id: str, export_file: str) -> Dict[str, Any]:
    """便捷函数：导入 Zotero 库"""
    importer = BatchImporter(notebook_id)
    await importer.initialize()
    try:
        return await importer.import_zotero_export(export_file)
    finally:
        await importer.close()


async def import_mendeley_library(notebook_id: str, export_file: str) -> Dict[str, Any]:
    """便捷函数：导入 Mendeley 库"""
    importer = BatchImporter(notebook_id)
    await importer.initialize()
    try:
        return await importer.import_mendeley_export(export_file)
    finally:
        await importer.close()
