import { useState, useRef, useEffect } from "react";
import { Send, Upload, FileText, ClipboardList, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage, Document } from "@/types";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

interface ChatInterfaceProps {
  messages: ChatMessage[];
  documents: Document[];
  onSendMessage: (message: string) => Promise<void>;
  onUploadDocuments: (files: FileList) => Promise<void>;
  onGenerateNotes: () => Promise<void>;
  onGeneratePracticeTest: () => Promise<void>;
  isLoading: boolean;
}

export const ChatInterface = ({
  messages,
  documents,
  onSendMessage,
  onUploadDocuments,
  onGenerateNotes,
  onGeneratePracticeTest,
  isLoading,
}: ChatInterfaceProps) => {
  const [input, setInput] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const message = input.trim();
    setInput("");
    await onSendMessage(message);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await onUploadDocuments(files);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header with action buttons */}
      <div className="p-4 border-b border-border bg-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Documents ({documents.length})</h3>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onGenerateNotes}
              disabled={isLoading || documents.length === 0}
            >
              <FileText className="h-4 w-4 mr-2" />
              Notes
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onGeneratePracticeTest}
              disabled={isLoading || documents.length === 0}
            >
              <ClipboardList className="h-4 w-4 mr-2" />
              Test
            </Button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {documents.map((doc, idx) => (
            <Badge key={idx} variant="secondary">
              {doc.filename}
            </Badge>
          ))}
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-12">
              <p className="text-lg mb-2">Upload documents to get started</p>
              <p className="text-sm">Ask questions, generate notes, or create practice tests</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex justify-end">
                  <div className="bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[80%]">
                    {msg.question}
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-muted rounded-lg px-4 py-2 max-w-[80%]">
                    {msg.answer}
                  </div>
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg px-4 py-2 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Thinking...</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t border-border bg-card">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask a question about your documents..."
            disabled={isLoading || documents.length === 0}
          />
          <Button onClick={handleSend} disabled={isLoading || !input.trim() || documents.length === 0}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.docx"
        className="hidden"
        onChange={handleFileUpload}
      />
    </div>
  );
};
