"use client";

import { motion } from "framer-motion";
import { FileText, Loader2, Upload } from "lucide-react";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

import { Button } from "@/components/ui/button";
import type { PipelineRunResponse } from "@lexguard/shared";

import { uploadAndAnalyze } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useAnalysisStore } from "@/stores/analysis-store";

interface DropzoneProps {
  onSuccess: (result: PipelineRunResponse, fileName: string, fileUrl: string) => void;
}

export function Dropzone({ onSuccess }: DropzoneProps) {
  const [uploading, setUploading] = useState(false);
  const setError = useAnalysisStore((s) => s.setError);

  const onDrop = useCallback(
    async (files: File[]) => {
      const file = files[0];
      if (!file) return;
      setUploading(true);
      setError(null);
      try {
        const fileUrl = URL.createObjectURL(file);
        const result = await uploadAndAnalyze(file);
        onSuccess(result, file.name, fileUrl);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [onSuccess, setError],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (f) => void onDrop(f),
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div
        {...getRootProps()}
        className={cn(
          "glass relative flex min-h-[220px] cursor-pointer flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed p-10 transition-colors",
          isDragActive ? "border-primary bg-primary/5" : "border-border/80 hover:border-primary/50",
          uploading && "pointer-events-none opacity-70",
        )}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <>
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Uploading & starting analysis…</p>
          </>
        ) : (
          <>
            <motion.div
              className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10"
              animate={isDragActive ? { scale: 1.05 } : { scale: 1 }}
            >
              <Upload className="h-7 w-7 text-primary" />
            </motion.div>
            <motion.div className="text-center">
              <p className="font-medium">Drop your contract here</p>
              <p className="mt-1 text-sm text-muted-foreground">PDF or DOCX · up to 50 MB</p>
            </motion.div>
            <Button type="button" variant="secondary" size="sm" className="gap-2">
              <FileText className="h-4 w-4" />
              Browse files
            </Button>
          </>
        )}
      </div>
    </motion.div>
  );
}
