import React, { useState, useRef, useEffect } from "react";
import {
    IconFile as FileType, IconMap as Map, IconDownload as Download,
    IconAlertCircle as AlertCircle, IconCheck as Check, IconX as X,
    IconSettings as Settings, IconCloudUpload as CloudUpload
} from "@tabler/icons-react";
import { cn } from "../lib/utils";

// --- Types ---
interface FileState {
    file: File | null;
    error: string | null;
}

// --- Components ---

const FileCard = ({
    file,
    onRemove,
    icon: Icon
}: {
    file: File;
    onRemove: () => void;
    icon: React.ElementType
}) => (
    <div className="flex items-center gap-4 p-4 bg-white/5 border border-white/10 rounded-2xl animate-fade-in group hover:bg-white/10 hover:border-white/20 transition-all duration-300 shadow-lg backdrop-blur-sm">
        <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-blue-500/20 rounded-xl text-indigo-300 ring-1 ring-white/10">
            <Icon size={24} />
        </div>
        <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate tracking-wide">{file.name}</p>
            <p className="text-xs text-white/50 font-medium">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
        </div>
        <button
            onClick={(e) => { e.stopPropagation(); onRemove(); }}
            className="p-2 hover:bg-red-500/20 rounded-xl text-white/40 hover:text-red-400 transition-colors"
        >
            <X size={18} />
        </button>
    </div>
);

const Dropzone = ({
    accept,
    label,
    sublabel,
    fileState,
    onFileSelect,
    icon: Icon,
    color = "indigo"
}: {
    accept: string;
    label: string;
    sublabel: string;
    fileState: FileState;
    onFileSelect: (file: File) => void;
    icon: React.ElementType;
    color?: "indigo" | "purple";
}) => {
    const inputRef = useRef<HTMLInputElement>(null);
    const [isDragging, setIsDragging] = useState(false);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setIsDragging(true);
        } else if (e.type === "dragleave") {
            setIsDragging(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            onFileSelect(e.dataTransfer.files[0]);
        }
    };

    const bgStyles = {
        indigo: "from-indigo-500/5 via-blue-500/5 to-transparent",
        purple: "from-purple-500/5 via-pink-500/5 to-transparent"
    };

    const borderStyles = {
        indigo: "group-hover:border-indigo-500/30",
        purple: "group-hover:border-purple-500/30"
    };

    return (
        <div className="relative group">
            <div
                onClick={() => !fileState.file && inputRef.current?.click()}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={cn(
                    "relative h-56 rounded-3xl border-2 border-dashed transition-all duration-500 flex flex-col items-center justify-center p-8 text-center cursor-pointer overflow-hidden",
                    isDragging
                        ? "border-indigo-400 bg-indigo-500/10 scale-[1.02] shadow-2xl"
                        : "border-white/10 hover:bg-white/[0.02]",
                    fileState.file ? "border-solid bg-white/5 cursor-default border-white/5" : bgStyles[color],
                    !fileState.file && borderStyles[color]
                )}
            >
                <input
                    ref={inputRef}
                    type="file"
                    className="hidden"
                    accept={accept}
                    onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
                />

                {fileState.file ? (
                    <div className="w-full relative z-10">
                        <FileCard
                            file={fileState.file}
                            onRemove={() => onFileSelect(null as any)}
                            icon={Icon}
                        />
                        <p className="mt-4 text-xs text-white/30 font-medium uppercase tracking-widest">Archivo cargado</p>
                    </div>
                ) : (
                    <>
                        <div className={cn(
                            "p-5 rounded-2xl bg-white/5 mb-5 group-hover:scale-110 group-hover:-rotate-3 transition-all duration-300 ring-1 ring-white/10",
                            isDragging && "scale-110"
                        )}>
                            <Icon className={cn(
                                "transition-colors duration-300",
                                color === "indigo" ? "text-indigo-400 group-hover:text-indigo-300" : "text-purple-400 group-hover:text-purple-300"
                            )} size={32} />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2 group-hover:text-white transition-colors tracking-tight">
                            {label}
                        </h3>
                        <p className="text-sm text-white/40 leading-relaxed max-w-[200px] mx-auto group-hover:text-white/60 transition-colors">
                            {sublabel}
                        </p>
                    </>
                )}
            </div>
        </div>
    );
};

// --- Main App ---

export default function ClimateMapApp() {
    const [pdf, setPdf] = useState<File | null>(null);
    const [shp, setShp] = useState<File | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [resultImage, setResultImage] = useState<string | null>(null);
    const [errorDetails, setErrorDetails] = useState<string | null>(null);
    const [showConfig, setShowConfig] = useState(false);
    const [backendUrl, setBackendUrl] = useState(import.meta.env.PUBLIC_BACKEND_URL || "");

    const resultRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to results
    useEffect(() => {
        if (resultImage && resultRef.current) {
            resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, [resultImage]);

    const handleProcess = async () => {
        if (!pdf || !shp) return;

        setIsProcessing(true);
        setResultImage(null);
        setErrorDetails(null);

        const formData = new FormData();
        formData.append("pdf", pdf);
        formData.append("shp", shp);

        const baseUrl = backendUrl || (typeof window !== "undefined" ? window.location.origin : "");
        const endpoint = `${baseUrl.replace(/\/$/, "")}/api/procesar/`;

        try {
            const response = await fetch(endpoint, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errJson = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errJson.detail || "Error processing files");
            }

            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);

            // Cleanup previous ObjectURL to prevent memory leak
            if (resultImage) {
                URL.revokeObjectURL(resultImage);
            }

            setResultImage(imageUrl);
        } catch (err: any) {
            setErrorDetails(`${err.message} (URL: ${endpoint})`);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleReset = () => {
        // Cleanup ObjectURL when resetting
        if (resultImage) {
            URL.revokeObjectURL(resultImage);
        }
        setPdf(null);
        setShp(null);
        setResultImage(null);
        setErrorDetails(null);
    };

    return (
        <div className="w-full max-w-6xl mx-auto space-y-12 animate-fade-in-up pb-20">

            {/* Main Processor Card */}
            <div className="relative group perspective-1000">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-[35px] blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                <div className="relative bg-[#131620] ring-1 ring-white/10 rounded-[30px] p-2 shadow-2xl">

                    {/* Toolbar */}
                    <div className="absolute top-6 right-6 z-20">
                        <button
                            onClick={() => setShowConfig(!showConfig)}
                            className="p-2.5 text-white/20 hover:text-white hover:bg-white/5 rounded-full transition-all"
                            title="Configuración API"
                        >
                            <Settings size={20} />
                        </button>
                    </div>

                    <div className="px-6 py-16 md:px-16 md:py-20">
                        {/* Header */}
                        <div className="text-center mb-16 space-y-4">
                            <h2 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight">
                                Generador <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">Inteligente</span>
                            </h2>
                            <p className="text-lg text-slate-400 max-w-xl mx-auto font-light leading-relaxed">
                                Sube el informe PDF y los archivos geográficos SHP. Nuestro algoritmo unificará los datos automáticamente.
                            </p>

                            {showConfig && (
                                <div className="max-w-md mx-auto mt-6 animate-fade-in p-1 bg-gradient-to-r from-white/5 to-transparent rounded-xl">
                                    <input
                                        value={backendUrl}
                                        onChange={(e) => setBackendUrl(e.target.value)}
                                        className="w-full bg-[#0b0d13] border-none rounded-lg px-4 py-3 text-white/80 placeholder:text-white/20 focus:ring-1 focus:ring-indigo-500 font-mono text-sm text-center"
                                        placeholder="http://localhost:8000"
                                    />
                                </div>
                            )}
                        </div>

                        {/* Upload Grid */}
                        <div className="grid md:grid-cols-2 gap-8 mb-12">
                            <Dropzone
                                accept="application/pdf"
                                label="Informe PDF"
                                sublabel="Arrastra el documento PDF con la tabla de zonas aquí."
                                fileState={{ file: pdf, error: null }}
                                onFileSelect={(f) => setPdf(f)}
                                icon={FileType}
                                color="indigo"
                            />
                            <Dropzone
                                accept=".zip,application/zip"
                                label="Geometría SHP"
                                sublabel="Sube el archivo .zip comprimido con todos los ficheros del SHP."
                                fileState={{ file: shp, error: null }}
                                onFileSelect={(f) => setShp(f)}
                                icon={Map}
                                color="purple"
                            />
                        </div>

                        {/* Action Area */}
                        <div className="flex flex-col items-center justify-center space-y-6">
                            <button
                                onClick={handleProcess}
                                disabled={!pdf || !shp || isProcessing}
                                className={cn(
                                    "relative px-10 py-5 rounded-2xl font-bold text-white shadow-xl transition-all duration-300 w-full md:w-auto min-w-[280px]",
                                    (!pdf || !shp)
                                        ? "bg-white/5 text-white/20 cursor-not-allowed shadow-none ring-1 ring-white/5"
                                        : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:shadow-indigo-500/40 hover:-translate-y-1 hover:scale-105 active:scale-95"
                                )}
                            >
                                <div className="flex items-center justify-center gap-3">
                                    {isProcessing ? (
                                        <>
                                            <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                            <span>Procesando Datos...</span>
                                        </>
                                    ) : (
                                        <>
                                            <CloudUpload size={22} className={cn("transition-all duration-300", (!pdf || !shp) ? "opacity-50" : "animate-bounce-subtle")} />
                                            <span>Generar Mapa</span>
                                        </>
                                    )}
                                </div>
                            </button>

                            {(!pdf || !shp) && (
                                <p className="text-xs text-white/20 font-medium uppercase tracking-widest animate-pulse">
                                    Sube ambos archivos para continuar
                                </p>
                            )}
                        </div>

                        {/* Error Message */}
                        {errorDetails && (
                            <div className="mt-10 p-6 bg-red-500/5 ring-1 ring-red-500/20 rounded-2xl flex items-start gap-4 text-red-200 animate-fade-in max-w-2xl mx-auto backdrop-blur-md">
                                <div className="p-2 bg-red-500/10 rounded-lg shrink-0">
                                    <AlertCircle size={24} className="text-red-400" />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-red-100 mb-1">Error en el proceso</h4>
                                    <p className="text-sm opacity-80 leading-relaxed font-mono text-xs">{errorDetails}</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Results View */}
            {resultImage && (
                <div ref={resultRef} className="scroll-mt-10 animate-fade-in-up duration-700">
                    <div className="relative group rounded-[30px] p-1 bg-gradient-to-b from-white/10 to-white/5 backdrop-blur-xl">
                        <div className="bg-[#0f111a] rounded-[28px] overflow-hidden shadow-2xl ring-1 ring-white/5">

                            {/* Result Header */}
                            <div className="px-8 py-6 border-b border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 bg-white/[0.02]">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-green-500/10 text-green-400">
                                        <Check size={20} />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-white text-lg">Mapa Generado con Éxito</h3>
                                        <p className="text-sm text-white/40">Zonificación completada</p>
                                    </div>
                                </div>

                                <div className="flex gap-3 w-full md:w-auto">
                                    <button
                                        onClick={handleReset}
                                        className="flex-1 md:flex-none px-5 py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-white hover:bg-white/10 transition-colors"
                                    >
                                        Reiniciar
                                    </button>
                                    <a
                                        href={resultImage}
                                        download="mapa_climatico.png"
                                        className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-bold transition-all shadow-lg hover:shadow-indigo-500/25"
                                    >
                                        <Download size={18} />
                                        Descargar PNG
                                    </a>
                                </div>
                            </div>

                            {/* Image Container */}
                            <div className="p-8 md:p-12 flex justify-center bg-[url('/grid.svg')] bg-center bg-repeat opacity-100">
                                <div className="relative rounded-xl overflow-hidden shadow-2xl border-4 border-white/5 bg-[#1a1d2d]">
                                    <img
                                        src={resultImage}
                                        alt="Mapa Climático"
                                        className="max-w-full h-auto max-h-[80vh] object-contain"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
