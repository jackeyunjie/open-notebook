import React, { useState } from 'react'
import { skillsApi, ReportGenerationRequest } from '../lib/skills-api'
import { BookOpen, FileText, TrendingUp, Map, Brain, Upload, Users, BarChart3 } from 'lucide-react'

const SkillsDashboard: React.FC = () => {
  const [notebookId, setNotebookId] = useState('')
  const [reportType, setReportType] = useState<ReportGenerationRequest['report_type']>('study_guide')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleGenerateReport = async () => {
    if (!notebookId) {
      setError('请输入 Notebook ID')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await skillsApi.generateReport({
        notebook_id: notebookId,
        report_type: reportType,
      })
      setResult(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  const reportTypes = [
    { value: 'study_guide', label: '学习指南', icon: <BookOpen className="w-5 h-5" />, desc: '快速了解某个主题' },
    { value: 'literature_review', label: '文献综述', icon: <FileText className="w-5 h-5" />, desc: '学术研究必备' },
    { value: 'research_digest', label: '研究简报', icon: <TrendingUp className="w-5 h-5" />, desc: '简洁的研究总结' },
    { value: 'weekly_trends', label: '周度趋势', icon: <BarChart3 className="w-5 h-5" />, desc: '追踪最新研究动态' },
    { value: 'concept_map', label: '概念图谱', icon: <Map className="w-5 h-5" />, desc: '可视化知识结构' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4 flex items-center justify-center gap-3">
            <Brain className="w-10 h-10 text-blue-600" />
            Open Notebook Skills Dashboard
          </h1>
          <p className="text-lg text-gray-600">P0/P1/C/B/A 功能一站式管理平台</p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* P0: Report Generator */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-6 h-6 text-blue-600" />
              P0 - 一键报告生成器
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notebook ID
                </label>
                <input
                  type="text"
                  value={notebookId}
                  onChange={(e) => setNotebookId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="输入 Notebook ID"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  报告类型
                </label>
                <div className="grid grid-cols-1 gap-2">
                  {reportTypes.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => setReportType(type.value as any)}
                      className={`p-3 rounded-lg border-2 transition-all text-left ${
                        reportType === type.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className={reportType === type.value ? 'text-blue-600' : 'text-gray-600'}>
                          {type.icon}
                        </span>
                        <div>
                          <div className="font-medium">{type.label}</div>
                          <div className="text-sm text-gray-500">{type.desc}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleGenerateReport}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {loading ? '生成中...' : '生成报告'}
              </button>
            </div>
          </div>

          {/* Other Features */}
          <div className="space-y-6">
            {/* P1: Visualization */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Map className="w-6 h-6 text-purple-600" />
                P1 - 可视化知识图谱
              </h3>
              <p className="text-gray-600 mb-4">思维导图、时间线、网络图、统计图表</p>
              <button className="w-full bg-purple-100 text-purple-700 py-2 px-4 rounded-lg hover:bg-purple-200 transition-colors font-medium">
                创建可视化
              </button>
            </div>

            {/* P1: Batch Import */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Upload className="w-6 h-6 text-green-600" />
                P1 - 批量导入工具
              </h3>
              <p className="text-gray-600 mb-4">文件夹、URL、Zotero、Mendeley</p>
              <button className="w-full bg-green-100 text-green-700 py-2 px-4 rounded-lg hover:bg-green-200 transition-colors font-medium">
                批量导入
              </button>
            </div>

            {/* A: Collaboration */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Users className="w-6 h-6 text-orange-600" />
                A - 协作功能
              </h3>
              <p className="text-gray-600 mb-4">共享、权限、评论、实时会话</p>
              <button className="w-full bg-orange-100 text-orange-700 py-2 px-4 rounded-lg hover:bg-orange-200 transition-colors font-medium">
                管理协作
              </button>
            </div>
          </div>
        </div>

        {/* Result Display */}
        {(result || error) && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">执行结果</h2>
            
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                ❌ {error}
              </div>
            )}

            {result && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700">
                  ✅ {result.message}
                </div>
                
                {result.note_id && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="font-medium text-blue-900">生成的 Note ID:</div>
                    <code className="text-blue-700 bg-blue-100 px-2 py-1 rounded mt-1 block">
                      {result.note_id}
                    </code>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* API Documentation Link */}
        <div className="text-center mt-8">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 underline"
          >
            📖 查看完整的 Swagger API 文档
          </a>
        </div>
      </div>
    </div>
  )
}

export default SkillsDashboard
