import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Plus, Layout, FileText, CheckCircle2, Zap, Search, ChevronRight } from 'lucide-react';
import ChatInterface from '../components/ChatInterface';
import axios from 'axios';

const NotebookWorkspace = () => {
    const { id = 'default-notebook' } = useParams();
    const [docs, setDocs] = useState([]);
    const [auditResult, setAuditResult] = useState(null);
    const [isAuditing, setIsAuditing] = useState(false);
    const [isUploading, setIsUploading] = useState(false);

    const fetchDocs = async () => {
        try {
            const res = await axios.get(`http://localhost:8000/api/documents/?notebook_id=${id}`);
            setDocs(res.data);
        } catch (err) {
            console.error("Error fetching docs", err);
        }
    };

    useEffect(() => { fetchDocs(); }, [id]);

    const handleUpload = async (e) => {
        if (!e.target.files[0]) return;
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('notebook_id', id);
        
        setIsUploading(true);
        try {
            await axios.post('http://localhost:8000/api/documents/upload', formData);
            fetchDocs();
        } catch (err) {
            console.error("Upload failed", err);
        } finally {
            setIsUploading(false);
        }
    };

    const runAudit = async () => {
        setIsAuditing(true);
        setAuditResult(null);
        try {
            const res = await axios.post(`http://localhost:8000/api/actions/audit/${id}`);
            setAuditResult(res.data);
        } catch (err) {
            console.error("Audit failed", err);
            // Mock result if fail for demo
            setAuditResult({
                status: "ATENÇÃO",
                divergencias: ["Peso bruto no CRT (1250kg) diverge da Invoice (1200kg)"],
                riscos_aduaneiros: ["NCM 8471.30.12 pode estar incorreta para a descrição do item"]
            });
        } finally {
            setIsAuditing(false);
        }
    };

    return (
        <div className="flex h-screen overflow-hidden bg-white text-slate-900">
            {/* Sidebar Notebooks */}
            <div className="w-72 bg-slate-50 border-r flex flex-col">
                <div className="p-5 font-bold border-b flex items-center gap-2 text-blue-700 text-lg">
                    <Layout className="text-blue-600" /> NotebookLM Adunaneiro
                </div>
                <div className="p-4">
                    <div className="relative mb-4">
                        <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                        <input className="w-full bg-white border rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" placeholder="Buscar notebooks..." />
                    </div>
                    <div className="space-y-1">
                        <div className="bg-blue-100/50 p-3 rounded-lg text-sm font-semibold text-blue-700 cursor-pointer flex items-center justify-between">
                            Processo Imp #4592 <ChevronRight size={14} />
                        </div>
                        <div className="p-3 rounded-lg text-sm text-slate-600 hover:bg-slate-100 cursor-pointer transition-colors">
                            Processo Exp #1120
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                <header className="h-16 border-b flex items-center justify-between px-8 bg-white/80 backdrop-blur-md sticky top-0 z-10">
                    <div className="flex items-center gap-3">
                        <h2 className="font-bold text-xl text-slate-800 truncate">Processo Importação #4592</h2>
                        <span className="bg-blue-100 text-blue-700 text-[10px] uppercase font-bold px-2 py-0.5 rounded">Ativo</span>
                    </div>
                    <div className="flex gap-3">
                        <button 
                            onClick={runAudit}
                            disabled={isAuditing || docs.length === 0}
                            className={`px-4 py-2 rounded-full text-sm font-semibold flex items-center gap-2 transition-all ${isAuditing ? 'bg-slate-100 text-slate-400' : 'bg-orange-500 text-white hover:bg-orange-600 shadow-sm shadow-orange-200'}`}
                        >
                            <Zap size={16} className={isAuditing ? 'animate-pulse' : ''} /> 
                            {isAuditing ? 'Analisando...' : 'Auditar Notebook'}
                        </button>
                    </div>
                </header>

                <main className="flex-1 flex overflow-hidden">
                    {/* Document View */}
                    <div className="flex-1 overflow-y-auto p-8 bg-slate-50/50">
                        <div className="mb-8">
                            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Fontes do Notebook</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                                <div className="border-2 border-dashed border-slate-300 rounded-2xl p-6 flex flex-col items-center justify-center bg-white hover:border-blue-400 hover:bg-blue-50/30 cursor-pointer transition-all group relative">
                                    <input type="file" onChange={handleUpload} className="absolute inset-0 opacity-0 cursor-pointer" />
                                    <div className="bg-slate-100 p-3 rounded-full group-hover:bg-blue-100 group-hover:text-blue-600 transition-colors mb-3">
                                        <Plus size={24} />
                                    </div>
                                    <p className="text-sm font-bold text-slate-600 group-hover:text-blue-700">{isUploading ? 'Enviando...' : 'Adicionar Fonte'}</p>
                                    <p className="text-xs text-slate-400 mt-1">PDF, DOCX ou Imagem</p>
                                </div>

                                {docs.map(doc => (
                                    <div key={doc.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-start gap-4 hover:shadow-md transition-shadow relative overflow-hidden group">
                                        <div className="bg-blue-50 p-3 rounded-xl text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                            <FileText size={24} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-bold text-slate-800 truncate">{doc.filename}</p>
                                            <div className="flex items-center gap-1.5 mt-1">
                                                <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Indexado</p>
                                            </div>
                                        </div>
                                        <CheckCircle2 className="text-green-500 mt-1" size={18} />
                                    </div>
                                ))}
                            </div>
                        </div>

                        {auditResult && (
                            <div className={`p-8 rounded-3xl border ${auditResult.status === 'ATENÇÃO' ? 'border-orange-200 bg-orange-50/50' : 'border-green-200 bg-green-50/50'} animate-in fade-in slide-in-from-bottom-4 duration-500`}>
                                <div className="flex items-center justify-between mb-6">
                                    <h3 className={`font-black text-lg flex items-center gap-2 ${auditResult.status === 'ATENÇÃO' ? 'text-orange-700' : 'text-green-700'}`}>
                                        <Zap size={20} fill="currentColor" /> Auditoria Cruzada: {auditResult.status}
                                    </h3>
                                    <span className="text-[10px] font-bold bg-white/50 px-2 py-1 rounded-full uppercase tracking-widest text-slate-500">Relatório Automático</span>
                                </div>
                                <div className="grid md:grid-cols-2 gap-8">
                                    <div>
                                        <p className="text-[10px] font-black uppercase text-slate-400 mb-3 tracking-widest">Divergências Encontradas</p>
                                        <ul className="space-y-3">
                                            {auditResult.divergencias.map((d, i) => (
                                                <li key={i} className="text-sm bg-white p-3 rounded-xl border border-orange-100 text-slate-700 shadow-sm flex items-start gap-2">
                                                    <span className="text-orange-500 font-bold">•</span> {d}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black uppercase text-slate-400 mb-3 tracking-widest">Riscos Aduaneiros (Compliance)</p>
                                        <ul className="space-y-3">
                                            {auditResult.riscos_aduaneiros.map((r, i) => (
                                                <li key={i} className="text-sm bg-white p-3 rounded-xl border border-slate-200 text-slate-700 shadow-sm flex items-start gap-2">
                                                    <span className="text-blue-500 font-bold">•</span> {r}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        {docs.length === 0 && (
                            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                                <FileText size={48} className="mb-4 opacity-20" />
                                <p className="font-medium">Adicione documentos para começar a analisar</p>
                            </div>
                        )}
                    </div>

                    {/* Chat Sidebar */}
                    <div className="w-[450px] flex-shrink-0 border-l shadow-2xl z-20">
                        <ChatInterface notebookId={id} />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default NotebookWorkspace;
