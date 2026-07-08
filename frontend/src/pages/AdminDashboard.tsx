import React, { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, ShieldCheck } from 'lucide-react';
import axios from 'axios';

const AdminDashboard = () => {
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchGlobalDocs = async () => {
        try {
            const res = await axios.get('http://localhost:8000/api/documents/');
            setDocs(res.data);
        } catch (err) {
            console.error("Error fetching docs", err);
        }
    };

    useEffect(() => { fetchGlobalDocs(); }, []);

    const handleUpload = async (e) => {
        if (!e.target.files[0]) return;
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('is_global', 'true');
        
        setLoading(true);
        try {
            await axios.post('http://localhost:8000/api/documents/upload', formData);
            fetchGlobalDocs();
        } catch (err) {
            console.error("Upload failed", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <header className="flex justify-between items-center mb-8 border-b pb-4">
                <h1 className="text-2xl font-bold flex items-center gap-2 text-slate-800">
                    <ShieldCheck className="text-blue-600" /> PM Logística - Base Global Admin
                </h1>
            </header>

            <div className="bg-white p-6 rounded-xl shadow-sm border mb-8">
                <h2 className="text-lg font-semibold mb-4 text-slate-700">Upload de Regulamentação (Siscomex, Receita, etc.)</h2>
                <div className="border-2 border-dashed border-slate-200 rounded-lg p-10 text-center hover:border-blue-400 transition-colors">
                    <input type="file" onChange={handleUpload} className="hidden" id="global-upload" />
                    <label htmlFor="global-upload" className="cursor-pointer flex flex-col items-center">
                        <Upload className="h-10 w-10 text-slate-400 mb-3" />
                        <span className="text-blue-600 font-medium">{loading ? 'Enviando...' : 'Clique para subir arquivos PDF'}</span>
                        <span className="text-xs text-slate-400 mt-1">Manuais fiscais, Legislação Siscomex</span>
                    </label>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {docs.map(doc => (
                    <div key={doc.id} className="p-4 bg-white border rounded-lg flex items-center justify-between shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center gap-3 overflow-hidden">
                            <div className="bg-blue-50 p-2 rounded text-blue-600">
                                <FileText size={20} />
                            </div>
                            <span className="font-medium text-slate-700 truncate">{doc.filename}</span>
                        </div>
                        <button className="text-slate-400 hover:text-red-500 hover:bg-red-50 p-2 rounded transition-colors">
                            <Trash2 size={18} />
                        </button>
                    </div>
                ))}
            </div>
            
            {docs.length === 0 && !loading && (
                <div className="text-center py-12 text-slate-400">
                    Nenhum documento na base global.
                </div>
            )}
        </div>
    );
};

export default AdminDashboard;
