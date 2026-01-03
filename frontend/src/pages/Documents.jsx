import { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  FileText, Upload, Trash2, Search, MessageSquare, 
  File, FileSpreadsheet, Code, Loader2, CheckCircle, XCircle,
  FolderOpen, Plus
} from 'lucide-react';
import api from '../utils/api';

const fileIcons = {
  pdf: FileText,
  docx: FileText,
  txt: FileText,
  md: FileText,
  csv: FileSpreadsheet,
  json: Code,
  default: File
};

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [chatMode, setChatMode] = useState(false);
  const [chatQuery, setChatQuery] = useState('');
  const [chatAnswer, setChatAnswer] = useState('');
  const [chatting, setChatting] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/documents/');
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    setUploading(true);
    
    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        await api.post('/documents/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } catch (error) {
        console.error('Error uploading file:', error);
      }
    }
    
    setUploading(false);
    fetchDocuments();
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'text/csv': ['.csv'],
      'application/json': ['.json']
    },
    maxSize: 10 * 1024 * 1024 // 10MB
  });

  const deleteDocument = async (id) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await api.delete(`/documents/${id}`);
      fetchDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const searchDocuments = async () => {
    if (!searchQuery.trim()) return;
    
    setSearching(true);
    try {
      const response = await api.post('/documents/query', {
        query: searchQuery,
        document_ids: selectedDocs.length > 0 ? selectedDocs : null,
        top_k: 5
      });
      setSearchResults(response.data.results);
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setSearching(false);
    }
  };

  const chatWithDocuments = async () => {
    if (!chatQuery.trim()) return;
    
    setChatting(true);
    setChatAnswer('');
    
    try {
      const response = await api.post('/documents/chat', null, {
        params: {
          query: chatQuery,
          document_ids: selectedDocs.length > 0 ? selectedDocs : null
        }
      });
      setChatAnswer(response.data.answer);
    } catch (error) {
      console.error('Error chatting:', error);
      setChatAnswer('Error getting response');
    } finally {
      setChatting(false);
    }
  };

  const toggleDocSelection = (id) => {
    setSelectedDocs(prev => 
      prev.includes(id) 
        ? prev.filter(d => d !== id)
        : [...prev, id]
    );
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing':
        return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const FileIcon = ({ type }) => {
    const Icon = fileIcons[type] || fileIcons.default;
    return <Icon className="w-8 h-8 text-cyan-400" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <FolderOpen className="w-8 h-8 text-cyan-400" />
              Documents
            </h1>
            <p className="text-gray-400 mt-1">Upload and chat with your documents</p>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => setChatMode(false)}
              className={`px-4 py-2 rounded-lg transition ${
                !chatMode 
                  ? 'bg-cyan-500 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <Search className="w-4 h-4 inline mr-2" />
              Search
            </button>
            <button
              onClick={() => setChatMode(true)}
              className={`px-4 py-2 rounded-lg transition ${
                chatMode 
                  ? 'bg-cyan-500 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <MessageSquare className="w-4 h-4 inline mr-2" />
              Chat
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Documents List */}
          <div className="lg:col-span-1 space-y-4">
            {/* Upload Zone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
                isDragActive 
                  ? 'border-cyan-400 bg-cyan-400/10' 
                  : 'border-gray-600 hover:border-gray-500 bg-gray-800/50'
              }`}
            >
              <input {...getInputProps()} />
              {uploading ? (
                <Loader2 className="w-8 h-8 mx-auto text-cyan-400 animate-spin" />
              ) : (
                <Upload className="w-8 h-8 mx-auto text-gray-400" />
              )}
              <p className="text-gray-400 mt-2">
                {isDragActive 
                  ? 'Drop files here...' 
                  : 'Drag & drop files or click to upload'}
              </p>
              <p className="text-gray-500 text-sm mt-1">
                PDF, DOCX, TXT, MD, CSV, JSON (max 10MB)
              </p>
            </div>

            {/* Documents */}
            <div className="bg-gray-800/50 rounded-xl p-4 max-h-[500px] overflow-y-auto">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Your Documents ({documents.length})
              </h3>
              
              {loading ? (
                <div className="text-center py-8">
                  <Loader2 className="w-6 h-6 mx-auto text-cyan-400 animate-spin" />
                </div>
              ) : documents.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No documents yet</p>
              ) : (
                <div className="space-y-2">
                  {documents.map(doc => (
                    <div
                      key={doc.id}
                      className={`p-3 rounded-lg cursor-pointer transition ${
                        selectedDocs.includes(doc.id)
                          ? 'bg-cyan-500/20 border border-cyan-500'
                          : 'bg-gray-700/50 hover:bg-gray-700 border border-transparent'
                      }`}
                      onClick={() => toggleDocSelection(doc.id)}
                    >
                      <div className="flex items-start gap-3">
                        <FileIcon type={doc.file_type} />
                        <div className="flex-1 min-w-0">
                          <p className="text-white font-medium truncate">{doc.name}</p>
                          <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                            <span>{formatFileSize(doc.file_size)}</span>
                            <span>•</span>
                            <span>{doc.chunk_count} chunks</span>
                            {getStatusIcon(doc.status)}
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteDocument(doc.id);
                          }}
                          className="p-1 text-gray-400 hover:text-red-400 transition"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {selectedDocs.length > 0 && (
              <p className="text-cyan-400 text-sm">
                {selectedDocs.length} document(s) selected
              </p>
            )}
          </div>

          {/* Search/Chat Panel */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800/50 rounded-xl p-6 h-full">
              {chatMode ? (
                /* Chat Mode */
                <div className="h-full flex flex-col">
                  <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-cyan-400" />
                    Chat with Documents
                  </h3>
                  
                  <div className="flex-1 bg-gray-900/50 rounded-lg p-4 mb-4 min-h-[300px]">
                    {chatAnswer ? (
                      <div className="prose prose-invert max-w-none">
                        <p className="text-gray-300 whitespace-pre-wrap">{chatAnswer}</p>
                      </div>
                    ) : (
                      <p className="text-gray-500 text-center mt-20">
                        Ask a question about your documents
                      </p>
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={chatQuery}
                      onChange={(e) => setChatQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && chatWithDocuments()}
                      placeholder="Ask a question..."
                      className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                    <button
                      onClick={chatWithDocuments}
                      disabled={chatting || !chatQuery.trim()}
                      className="px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                    >
                      {chatting ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        'Ask'
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                /* Search Mode */
                <div className="h-full flex flex-col">
                  <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <Search className="w-5 h-5 text-cyan-400" />
                    Semantic Search
                  </h3>
                  
                  <div className="flex gap-2 mb-4">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && searchDocuments()}
                      placeholder="Search in documents..."
                      className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                    <button
                      onClick={searchDocuments}
                      disabled={searching || !searchQuery.trim()}
                      className="px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                    >
                      {searching ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        'Search'
                      )}
                    </button>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto space-y-3">
                    {searchResults.length === 0 ? (
                      <p className="text-gray-500 text-center mt-20">
                        Search results will appear here
                      </p>
                    ) : (
                      searchResults.map((result, idx) => (
                        <div
                          key={idx}
                          className="bg-gray-700/50 rounded-lg p-4"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-cyan-400 text-sm">
                              Document #{result.document_id} • Chunk {result.chunk_index}
                            </span>
                            <span className="text-gray-400 text-sm">
                              Score: {(result.score * 100).toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-gray-300 text-sm">{result.content}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
