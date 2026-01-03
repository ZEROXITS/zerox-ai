import { useState, useEffect } from 'react';
import { 
  Search, Calculator, Cloud, BookOpen, Code, Link, 
  Globe, Calendar, Loader2, ChevronDown, ChevronUp,
  Zap, X
} from 'lucide-react';
import api from '../utils/api';

const pluginIcons = {
  web_search: Search,
  calculator: Calculator,
  weather: Cloud,
  wikipedia: BookOpen,
  code_executor: Code,
  url_summarizer: Link,
  translator: Globe,
  datetime: Calendar
};

export default function PluginsPanel({ onUseResult, isOpen, onClose }) {
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlugin, setSelectedPlugin] = useState(null);
  const [params, setParams] = useState({});
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    fetchPlugins();
  }, []);

  const fetchPlugins = async () => {
    try {
      const response = await api.get('/plugins/');
      setPlugins(response.data.plugins);
    } catch (error) {
      console.error('Error fetching plugins:', error);
    } finally {
      setLoading(false);
    }
  };

  const executePlugin = async () => {
    if (!selectedPlugin) return;
    
    setExecuting(true);
    setResult(null);
    
    try {
      const response = await api.post('/plugins/execute', {
        plugin_name: selectedPlugin.name,
        params
      });
      setResult(response.data.result);
    } catch (error) {
      setResult({ error: error.response?.data?.detail || 'Error executing plugin' });
    } finally {
      setExecuting(false);
    }
  };

  const handleUseResult = () => {
    if (result && onUseResult) {
      let text = '';
      
      if (selectedPlugin.name === 'web_search' && result.results) {
        text = result.results.map(r => `- ${r.title}: ${r.url}`).join('\n');
      } else if (selectedPlugin.name === 'wikipedia' && result.summary) {
        text = `${result.title}\n\n${result.summary}`;
      } else if (selectedPlugin.name === 'weather') {
        text = `Weather in ${result.location}: ${result.condition}, ${result.temperature_c}°C`;
      } else if (selectedPlugin.name === 'calculator') {
        text = `${result.expression} = ${result.result}`;
      } else if (result.output) {
        text = result.output;
      } else if (result.content) {
        text = result.content;
      } else {
        text = JSON.stringify(result, null, 2);
      }
      
      onUseResult(text);
    }
  };

  const PluginIcon = ({ name }) => {
    const Icon = pluginIcons[name] || Zap;
    return <Icon className="w-5 h-5" />;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-gray-800 border-l border-gray-700 shadow-xl z-40 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <Zap className="w-5 h-5 text-cyan-400" />
          Plugins
        </h3>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 mx-auto text-cyan-400 animate-spin" />
          </div>
        ) : (
          <>
            {/* Plugin List */}
            <div className="space-y-2 mb-4">
              {plugins.map(plugin => (
                <button
                  key={plugin.name}
                  onClick={() => {
                    setSelectedPlugin(plugin);
                    setParams({});
                    setResult(null);
                  }}
                  className={`w-full p-3 rounded-lg text-left transition flex items-center gap-3 ${
                    selectedPlugin?.name === plugin.name
                      ? 'bg-cyan-500/20 border border-cyan-500'
                      : 'bg-gray-700/50 hover:bg-gray-700 border border-transparent'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${
                    selectedPlugin?.name === plugin.name
                      ? 'bg-cyan-500 text-white'
                      : 'bg-gray-600 text-gray-300'
                  }`}>
                    <PluginIcon name={plugin.name} />
                  </div>
                  <div>
                    <p className="text-white text-sm font-medium">{plugin.display_name}</p>
                    <p className="text-gray-400 text-xs">{plugin.description}</p>
                  </div>
                </button>
              ))}
            </div>

            {/* Selected Plugin */}
            {selectedPlugin && (
              <div className="bg-gray-700/50 rounded-lg p-4">
                <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                  <PluginIcon name={selectedPlugin.name} />
                  {selectedPlugin.display_name}
                </h4>

                {/* Parameters */}
                <div className="space-y-3 mb-4">
                  {Object.entries(selectedPlugin.schema?.properties || {}).map(([key, prop]) => (
                    <div key={key}>
                      <label className="block text-gray-400 text-xs mb-1">
                        {key}
                        {selectedPlugin.schema?.required?.includes(key) && (
                          <span className="text-red-400 ml-1">*</span>
                        )}
                      </label>
                      {prop.type === 'integer' ? (
                        <input
                          type="number"
                          value={params[key] || prop.default || ''}
                          onChange={(e) => setParams({ ...params, [key]: parseInt(e.target.value) })}
                          placeholder={prop.description}
                          className="w-full bg-gray-600 text-white rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
                        />
                      ) : (
                        <input
                          type="text"
                          value={params[key] || ''}
                          onChange={(e) => setParams({ ...params, [key]: e.target.value })}
                          placeholder={prop.description}
                          className="w-full bg-gray-600 text-white rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
                        />
                      )}
                    </div>
                  ))}
                </div>

                <button
                  onClick={executePlugin}
                  disabled={executing}
                  className="w-full py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50 transition flex items-center justify-center gap-2"
                >
                  {executing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      Execute
                    </>
                  )}
                </button>

                {/* Result */}
                {result && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-xs">Result</span>
                      {result.success !== false && (
                        <button
                          onClick={handleUseResult}
                          className="text-cyan-400 text-xs hover:text-cyan-300"
                        >
                          Use in chat
                        </button>
                      )}
                    </div>
                    <div className="bg-gray-800 rounded p-3 max-h-48 overflow-y-auto">
                      {result.error ? (
                        <p className="text-red-400 text-sm">{result.error}</p>
                      ) : (
                        <pre className="text-gray-300 text-xs whitespace-pre-wrap">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
