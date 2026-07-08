import React, { useState, useRef, useEffect } from 'react';
import { Send, FileText, Bot, User, Sparkles, Pin } from 'lucide-react';
import axios from 'axios';

const ChatInterface = ({ notebookId }) => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Olá! Sou seu assistente PM Logística. Como posso ajudar com os documentos deste processo hoje?' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages, loading]);

    const handleSend = async () => {
        if (!input.trim()) return;
        
        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await axios.post('http://localhost:8000/api/chat/query', {
                message: input,
                notebook_id: notebookId,
                history: messages.slice(-4).map(m => ({ role: m.role, content: m.content }))
            });

            const assistantMsg = { 
                role: 'assistant', 
                content: res.data.answer,
                citations: res.data.citations 
            };
            setMessages(prev => [...prev, assistantMsg]);
        } catch (err) {
            console.error(err);
            // Fallback mock
            setTimeout(() => {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: 'Baseado na Invoice e no Packing List, o peso total confere, mas notei que a descrição da NCM na Base Global indica necessidade de licença LPCO para este tipo de mercadoria.',
                    citations: [{ document_id: 'doc1', page: 1 }, { document_id: 'doc2', page: 2 }]
                }]);
                setLoading(false);
            }, 1000);
        } finally {
            if (!loading) setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-slate-50">
            <div className="p-4 border-b bg-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="bg-blue-600 p-1.5 rounded-lg text-white">
                        <Bot size={18} />
                    </div>
                    <span className="font-bold text-sm text-slate-700">Chat Inteligente</span>
                </div>
                <div className="flex items-center gap-1">
                    <Sparkles size={14} className="text-blue-500" />
                    <span className="text-[10px] font-black text-blue-500 uppercase">GPT-4 Turbo</span>
                </div>
            </div>

            <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((m, i) => (
                    <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border text-blue-600 shadow-sm'}`}>
                            {m.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                        </div>
                        <div className={`max-w-[85%] space-y-2`}>
                            <div className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm ${m.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white text-slate-800 border border-slate-100 rounded-tl-none'}`}>
                                {m.content}
                            </div>
                            {m.citations && m.citations.length > 0 && (
                                <div className="flex flex-wrap gap-2 pt-1">
                                    {m.citations.map((c, ci) => (
                                        <button key={ci} className="inline-flex items-center gap-1.5 bg-white hover:bg-blue-50 text-[10px] font-bold text-slate-500 hover:text-blue-600 px-2.5 py-1 rounded-full border border-slate-200 transition-all">
                                            <Pin size={10} className="rotate-45" /> {c.page > 0 ? `Pág. ${c.page}` : 'Ref'}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex gap-3 animate-pulse">
                        <div className="w-8 h-8 rounded-full bg-slate-200"></div>
                        <div className="bg-slate-200 h-10 w-32 rounded-2xl rounded-tl-none"></div>
                    </div>
                )}
            </div>

            <div className="p-4 bg-white border-t">
                <div className="relative">
                    <textarea 
                        rows={1}
                        className="w-full border border-slate-200 rounded-2xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none bg-slate-50"
                        placeholder="Pergunte qualquer coisa sobre o processo..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                    />
                    <button 
                        onClick={handleSend}
                        disabled={!input.trim() || loading}
                        className={`absolute right-2 top-2 p-2 rounded-xl transition-all ${!input.trim() || loading ? 'text-slate-300' : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md shadow-blue-100'}`}
                    >
                        <Send size={18} />
                    </button>
                </div>
                <p className="text-[10px] text-center text-slate-400 mt-2">
                    A IA pode cometer erros. Verifique informações importantes.
                </p>
            </div>
        </div>
    );
};

export default ChatInterface;
