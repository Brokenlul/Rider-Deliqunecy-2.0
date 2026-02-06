import { useState, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { 
  Upload, 
  FileText, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle, 
  ChevronRight,
  Download,
  RefreshCw,
  Info,
  Shield,
  DollarSign,
  BarChart3,
  AlertTriangle,
  XCircle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Score Gauge Component
const ScoreGauge = ({ score, maxScore = 100 }) => {
  const percentage = (score / maxScore) * 100;
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  const getScoreColor = () => {
    if (score >= 80) return '#10B981';
    if (score >= 60) return '#00FFFF';
    if (score >= 40) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <div className="relative w-48 h-48 mx-auto">
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
        {/* Background circle */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="#333333"
          strokeWidth="8"
        />
        {/* Progress circle */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={getScoreColor()}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="score-gauge-circle"
          style={{
            filter: `drop-shadow(0 0 10px ${getScoreColor()})`
          }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-5xl font-heading font-bold text-white">{Math.round(score)}</span>
        <span className="text-sm text-gray-400 mt-1">/ {maxScore}</span>
      </div>
    </div>
  );
};

// Tier Badge Component
const TierBadge = ({ tier, className = "" }) => {
  const getBadgeStyles = () => {
    switch (tier?.toLowerCase()) {
      case 'premium':
        return 'bg-emerald-500 text-black';
      case 'standard':
        return 'bg-lily-cyan text-black';
      case 'watchlist':
        return 'bg-amber-500 text-black';
      case 'reject':
        return 'bg-red-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  return (
    <span className={`px-4 py-1.5 rounded-full text-sm font-semibold ${getBadgeStyles()} ${className}`}>
      {tier}
    </span>
  );
};

// Metric Card Component
const MetricCard = ({ metric, delay = 0 }) => {
  const getMetricIcon = (name) => {
    const iconMap = {
      'Income Stability': TrendingUp,
      'Weekly Affordability': DollarSign,
      'Liquidity Behavior': BarChart3,
      'Expense Discipline': Shield,
      'Negative Events': AlertTriangle,
    };
    return iconMap[name] || Info;
  };

  const Icon = getMetricIcon(metric.metric);
  const percentage = metric.percentage;

  return (
    <div 
      className="bg-lily-surface border border-lily-border rounded-lg p-5 card-hover animate-fade-in"
      style={{ animationDelay: `${delay}ms` }}
      data-testid={`metric-card-${metric.metric.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-black/50">
            <Icon className="w-5 h-5 text-lily-cyan" />
          </div>
          <h4 className="font-heading font-semibold text-white">{metric.metric}</h4>
        </div>
        <span className="font-mono text-lg font-bold text-lily-cyan">
          {metric.points.toFixed(1)}/{metric.max_points}
        </span>
      </div>
      
      <div className="progress-bar h-2 rounded-full mb-3">
        <div 
          className="progress-bar-fill h-full rounded-full"
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      <p className="text-sm text-gray-400 mb-2">{metric.explanation}</p>
      <p className="text-xs text-lily-cyan-light">{metric.score_reason}</p>
    </div>
  );
};

// File Dropzone Component
const FileDropzone = ({ onFileSelect, isLoading, selectedFile }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      onFileSelect(file);
    } else {
      toast.error('Please upload a PDF file');
    }
  }, [onFileSelect]);

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <div
      className={`dropzone rounded-xl p-8 text-center cursor-pointer ${isDragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => document.getElementById('file-input').click()}
      data-testid="file-dropzone"
    >
      <input
        id="file-input"
        type="file"
        accept=".pdf"
        onChange={handleFileInput}
        className="hidden"
        disabled={isLoading}
      />
      
      {selectedFile ? (
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-lily-cyan/10 flex items-center justify-center">
            <FileText className="w-8 h-8 text-lily-cyan" />
          </div>
          <div>
            <p className="text-white font-medium">{selectedFile.name}</p>
            <p className="text-gray-400 text-sm mt-1">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
          <p className="text-lily-cyan text-sm">Click to change file</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-lily-surface flex items-center justify-center">
            <Upload className="w-8 h-8 text-lily-cyan" />
          </div>
          <div>
            <p className="text-white font-medium">Drop your bank statement here</p>
            <p className="text-gray-400 text-sm mt-1">or click to browse</p>
          </div>
          <p className="text-gray-500 text-xs">PDF files only, max 10MB</p>
        </div>
      )}
    </div>
  );
};

// Transactions Table Component
const TransactionsTable = ({ transactions, onDownloadCSV }) => {
  const displayTransactions = transactions?.slice(0, 50) || [];

  const downloadCSV = () => {
    if (!transactions || transactions.length === 0) return;
    
    const headers = ['Date', 'Description', 'Debit', 'Credit', 'Balance'];
    const rows = transactions.map(t => [
      t.date,
      `"${t.description}"`,
      t.debit || 0,
      t.credit || 0,
      t.balance || ''
    ]);
    
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'transactions.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-lily-surface border border-lily-border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-lily-border">
        <h3 className="font-heading font-semibold text-white">Parsed Transactions</h3>
        <button
          onClick={downloadCSV}
          className="flex items-center gap-2 px-3 py-1.5 text-sm btn-outline rounded-lg"
          data-testid="download-csv-btn"
        >
          <Download className="w-4 h-4" />
          Download CSV
        </button>
      </div>
      
      <div className="overflow-x-auto max-h-96">
        <table className="w-full table-dark">
          <thead className="sticky top-0">
            <tr>
              <th className="text-left p-3">Date</th>
              <th className="text-left p-3">Description</th>
              <th className="text-right p-3">Debit</th>
              <th className="text-right p-3">Credit</th>
              <th className="text-right p-3">Balance</th>
            </tr>
          </thead>
          <tbody>
            {displayTransactions.map((txn, idx) => (
              <tr key={idx}>
                <td className="p-3 font-mono text-sm text-gray-300">{txn.date}</td>
                <td className="p-3 text-sm text-white max-w-xs truncate">{txn.description}</td>
                <td className="p-3 font-mono text-sm text-red-400 text-right">
                  {txn.debit > 0 ? `₹${txn.debit.toLocaleString()}` : '-'}
                </td>
                <td className="p-3 font-mono text-sm text-emerald-400 text-right">
                  {txn.credit > 0 ? `₹${txn.credit.toLocaleString()}` : '-'}
                </td>
                <td className="p-3 font-mono text-sm text-gray-400 text-right">
                  {txn.balance ? `₹${txn.balance.toLocaleString()}` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {transactions && transactions.length > 50 && (
        <div className="p-3 text-center text-sm text-gray-400 border-t border-lily-border">
          Showing 50 of {transactions.length} transactions
        </div>
      )}
    </div>
  );
};

// Recommendations Card Component
const RecommendationsCard = ({ recommendations, tier }) => {
  const pricing = recommendations?.pricing || {};
  const operational = recommendations?.operational || [];
  const riskFactors = recommendations?.risk_factors || [];

  return (
    <div className="bg-lily-surface border border-lily-border rounded-lg p-6">
      <h3 className="font-heading font-semibold text-white text-lg mb-4 flex items-center gap-2">
        <Shield className="w-5 h-5 text-lily-cyan" />
        Recommendations
      </h3>
      
      {pricing.recommendation ? (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg mb-4">
          <p className="text-red-400 font-medium">{pricing.recommendation}</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-black/30 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Recommended Weekly Rent</p>
            <p className="font-mono text-2xl text-lily-cyan font-bold">
              ₹{pricing.recommended_weekly_rent?.toLocaleString() || '-'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {pricing.rent_multiplier < 1 ? 'Discounted' : pricing.rent_multiplier > 1 ? 'Premium' : 'Standard'} rate
            </p>
          </div>
          <div className="bg-black/30 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Security Deposit</p>
            <p className="font-mono text-2xl text-lily-cyan-light font-bold">
              ₹{pricing.security_deposit_amount?.toLocaleString() || '-'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {pricing.security_deposit_weeks} week(s)
            </p>
          </div>
        </div>
      )}
      
      {operational.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Operational Notes</h4>
          <ul className="space-y-2">
            {operational.map((note, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-400">
                <Info className="w-4 h-4 text-lily-cyan mt-0.5 flex-shrink-0" />
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {riskFactors.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Risk Factors</h4>
          <div className="flex flex-wrap gap-2">
            {riskFactors.map((factor, idx) => (
              <span key={idx} className="px-2 py-1 text-xs bg-amber-500/10 text-amber-400 rounded-full border border-amber-500/30">
                {factor}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [step, setStep] = useState(1);
  const [selectedFile, setSelectedFile] = useState(null);
  const [weeklyRent, setWeeklyRent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [transactions, setTransactions] = useState([]);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      toast.error('Please upload a bank statement PDF');
      return;
    }
    if (!weeklyRent || parseFloat(weeklyRent) <= 0) {
      toast.error('Please enter a valid weekly rent amount');
      return;
    }

    setIsLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('weekly_rent', weeklyRent);

      const response = await axios.post(`${API}/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        setAnalysisResult(response.data);
        // Extract transactions from metrics detail
        const txnSample = response.data.metrics_detail?.income_stability?.monthly_totals ? 
          Object.entries(response.data.metrics_detail.income_stability.monthly_totals).map(([month, amount]) => ({
            date: month,
            description: 'Monthly Credit Total',
            debit: 0,
            credit: amount,
            balance: null
          })) : [];
        setTransactions(txnSample);
        setStep(2);
        toast.success('Analysis complete!');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      const errorMsg = error.response?.data?.detail || 'Analysis failed. Please try again.';
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunDemo = async () => {
    setIsLoading(true);
    
    try {
      const response = await axios.get(`${API}/synthetic-demo`, {
        params: { weekly_rent: weeklyRent || 900 }
      });

      if (response.data.success) {
        setAnalysisResult(response.data);
        setTransactions(response.data.transactions_sample || []);
        setStep(2);
        toast.success('Demo analysis complete!');
      }
    } catch (error) {
      console.error('Demo error:', error);
      toast.error('Demo failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setStep(1);
    setSelectedFile(null);
    setWeeklyRent('');
    setAnalysisResult(null);
    setTransactions([]);
  };

  return (
    <div className="min-h-screen bg-black">
      <Toaster 
        position="top-right" 
        theme="dark"
        toastOptions={{
          style: {
            background: '#1A1A1A',
            border: '1px solid #333333',
            color: '#ffffff',
          }
        }}
      />
      
      {/* Header */}
      <header className="border-b border-lily-border bg-lily-surface/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-lily-cyan flex items-center justify-center">
                <span className="text-black font-heading font-bold text-xl">L</span>
              </div>
              <div>
                <h1 className="font-heading font-bold text-xl text-white tracking-tight">Lily's Score</h1>
                <p className="text-xs text-gray-400">by Lilypad</p>
              </div>
            </div>
            
            {step === 2 && (
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 btn-outline rounded-lg text-sm"
                data-testid="new-analysis-btn"
              >
                <RefreshCw className="w-4 h-4" />
                New Analysis
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {step === 1 && (
          <div className="max-w-2xl mx-auto animate-fade-in">
            {/* Welcome Section */}
            <div className="text-center mb-10">
              <h2 className="font-heading text-4xl font-bold text-white mb-4">
                Rider Credit Assessment
              </h2>
              <p className="text-gray-400 text-lg">
                Upload a bank statement to get an instant financial risk score
              </p>
            </div>

            {/* Upload Card */}
            <div className="bg-lily-surface border border-lily-border rounded-xl p-6 mb-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-lily-cyan text-black flex items-center justify-center font-bold text-sm">1</div>
                <h3 className="font-heading font-semibold text-white text-lg">Upload Bank Statement</h3>
              </div>
              
              <FileDropzone 
                onFileSelect={handleFileSelect}
                isLoading={isLoading}
                selectedFile={selectedFile}
              />
            </div>

            {/* Weekly Rent Input */}
            <div className="bg-lily-surface border border-lily-border rounded-xl p-6 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-full bg-lily-cyan text-black flex items-center justify-center font-bold text-sm">2</div>
                <h3 className="font-heading font-semibold text-white text-lg">Enter Weekly Rent</h3>
              </div>
              
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">₹</span>
                <input
                  type="number"
                  value={weeklyRent}
                  onChange={(e) => setWeeklyRent(e.target.value)}
                  placeholder="Enter weekly rent amount"
                  className="w-full pl-10 pr-4 py-3 input-dark rounded-lg"
                  data-testid="weekly-rent-input"
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                This is used to calculate affordability ratio
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={handleAnalyze}
                disabled={isLoading || !selectedFile}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-4 btn-primary rounded-xl text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="analyze-btn"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    Analyze Statement
                    <ChevronRight className="w-5 h-5" />
                  </>
                )}
              </button>
              
              <button
                onClick={handleRunDemo}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 px-6 py-4 btn-outline rounded-xl font-semibold disabled:opacity-50"
                data-testid="demo-btn"
              >
                Run Demo
              </button>
            </div>

            {/* Info Note */}
            <div className="mt-6 p-4 bg-lily-cyan/5 border border-lily-cyan/20 rounded-lg">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-lily-cyan flex-shrink-0 mt-0.5" />
                <div className="text-sm text-gray-400">
                  <p className="font-medium text-lily-cyan-light mb-1">Supported Formats</p>
                  <p>Works with text-based PDFs from major Indian banks (HDFC, ICICI, SBI, Axis). OCR fallback available for scanned statements.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 2 && analysisResult && (
          <div className="animate-slide-up">
            {/* Score Hero Section */}
            <div className="bg-lily-surface border border-lily-border rounded-xl p-8 mb-8">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
                {/* Score Gauge */}
                <div className="lg:col-span-1 text-center">
                  <ScoreGauge score={analysisResult.final_score} />
                  <p className="text-gray-400 mt-4">Lily's Score</p>
                </div>
                
                {/* Tier Info */}
                <div className="lg:col-span-2">
                  <div className="flex items-center gap-4 mb-4">
                    <TierBadge tier={analysisResult.tier} />
                    {analysisResult.used_ocr && (
                      <span className="px-3 py-1 text-xs bg-amber-500/10 text-amber-400 rounded-full border border-amber-500/30">
                        OCR Used
                      </span>
                    )}
                  </div>
                  
                  <h2 className="font-heading text-2xl font-bold text-white mb-2">
                    {analysisResult.tier_description}
                  </h2>
                  
                  <p className="text-gray-400 mb-4">{analysisResult.summary}</p>
                  
                  <div className="flex flex-wrap gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">Transactions:</span>
                      <span className="font-mono text-white">{analysisResult.transactions_count}</span>
                    </div>
                    {analysisResult.parser_confidence !== undefined && (
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">Parser Confidence:</span>
                        <span className="font-mono text-white">{(analysisResult.parser_confidence * 100).toFixed(0)}%</span>
                      </div>
                    )}
                    {analysisResult.demo_mode && (
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 text-xs bg-lily-cyan/10 text-lily-cyan rounded border border-lily-cyan/30">
                          Demo Mode
                        </span>
                      </div>
                    )}
                    {analysisResult.rider_id && (
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">Rider ID:</span>
                        <span className="font-mono text-lily-cyan">{analysisResult.rider_id}</span>
                      </div>
                    )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {analysisResult.breakdown?.map((metric, idx) => (
                <MetricCard key={metric.metric} metric={metric} delay={idx * 100} />
              ))}
            </div>

            {/* Recommendations & Transactions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RecommendationsCard 
                recommendations={analysisResult.recommendations}
                tier={analysisResult.tier}
              />
              
              {transactions.length > 0 && (
                <TransactionsTable transactions={transactions} />
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-lily-border mt-16 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-gray-500">
            <p>© 2024 Lilypad. Lily's Score MVP v1.0</p>
            <p>Bank statements are processed in-memory and not stored permanently.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
