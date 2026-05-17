"use client";

import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Worker must match react-pdf's bundled pdfjs API version (see pdfjs.version).
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

interface PdfViewerProps {
  fileUrl: string | null;
  fileName?: string | null;
  jumpToPage?: number | null;
  className?: string;
}

export function PdfViewer({ fileUrl, fileName, jumpToPage, className }: PdfViewerProps) {
  const [numPages, setNumPages] = useState(0);
  const [page, setPage] = useState(1);
  const [scale, setScale] = useState(1);
  const isPdf = fileName?.toLowerCase().endsWith(".pdf") ?? false;

  const onLoadSuccess = useCallback(({ numPages: n }: { numPages: number }) => {
    setNumPages(n);
    setPage(1);
  }, []);

  useEffect(() => {
    if (jumpToPage != null && jumpToPage >= 1) {
      setPage(jumpToPage);
    }
  }, [jumpToPage]);

  if (!fileUrl) {
    return (
      <div className={cn("glass flex flex-1 items-center justify-center rounded-xl", className)}>
        <p className="text-sm text-muted-foreground">No document loaded</p>
      </div>
    );
  }

  if (!isPdf) {
    return (
      <div className={cn("glass flex flex-1 flex-col items-center justify-center gap-2 rounded-xl p-8", className)}>
        <p className="text-sm font-medium">DOCX preview</p>
        <p className="max-w-xs text-center text-xs text-muted-foreground">
          Word documents are parsed server-side. Review extracted clauses in the center panel.
        </p>
      </div>
    );
  }

  return (
    <motion.div
      className={cn("glass flex flex-1 flex-col overflow-hidden rounded-xl", className)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="flex items-center justify-between border-b border-border/60 px-3 py-2">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="min-w-[80px] text-center text-xs text-muted-foreground">
            {page} / {numPages || "—"}
          </span>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            disabled={page >= numPages}
            onClick={() => setPage((p) => Math.min(numPages, p + 1))}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setScale((s) => Math.max(0.5, s - 0.15))}
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="w-10 text-center text-xs text-muted-foreground">{Math.round(scale * 100)}%</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setScale((s) => Math.min(2, s + 0.15))}
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <div className="flex flex-1 justify-center overflow-auto bg-secondary/30 p-4">
        <Document file={fileUrl} onLoadSuccess={onLoadSuccess} loading={<PdfLoading />}>
          <Page
            pageNumber={page}
            scale={scale}
            className="shadow-lg"
            renderTextLayer
            renderAnnotationLayer
          />
        </Document>
      </div>
    </motion.div>
  );
}

function PdfLoading() {
  return (
    <div className="flex h-64 items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>
  );
}
