import { useState, useEffect } from "react";
import { SessionList } from "@/components/SessionList";
import { ChatInterface } from "@/components/ChatInterface";
import { api } from "@/services/api";
import { getUserId, getCurrentSessionId, setCurrentSessionId, clearCurrentSession } from "@/utils/localStorage";
import { Session } from "@/types";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const Index = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const userId = getUserId();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await api.getSessions(userId);
      setSessions(response.sessions);

      const savedSessionId = getCurrentSessionId();
      if (savedSessionId && response.sessions.some((s: Session) => s.session_id === savedSessionId)) {
        await loadSession(savedSessionId);
      } else if (response.sessions.length > 0) {
        await loadSession(response.sessions[0].session_id);
      }
    } catch (error) {
      toast.error("Failed to load sessions");
      console.error(error);
    } finally {
      setIsInitializing(false);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      const response = await api.getSession(userId, sessionId);
      setCurrentSession(response.session);
      setCurrentSessionId(sessionId);
    } catch (error) {
      toast.error("Failed to load session");
      console.error(error);
    }
  };

  const handleCreateSession = async () => {
    try {
      const response = await api.createSession(userId, `Chat ${sessions.length + 1}`);
      setSessions([response.session, ...sessions]);
      setCurrentSession(response.session);
      setCurrentSessionId(response.session.session_id);
      toast.success("New session created");
    } catch (error) {
      toast.error("Failed to create session");
      console.error(error);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await api.deleteSession(userId, sessionId);
      setSessions(sessions.filter((s) => s.session_id !== sessionId));
      if (currentSession?.session_id === sessionId) {
        setCurrentSession(null);
        clearCurrentSession();
        if (sessions.length > 1) {
          const nextSession = sessions.find((s) => s.session_id !== sessionId);
          if (nextSession) {
            await loadSession(nextSession.session_id);
          }
        }
      }
      toast.success("Session deleted");
    } catch (error) {
      toast.error("Failed to delete session");
      console.error(error);
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!currentSession) return;

    setIsLoading(true);
    try {
      const response = await api.sendMessage(userId, currentSession.session_id, message);
      await loadSession(currentSession.session_id);
      await loadSessions();
    } catch (error) {
      toast.error("Failed to send message");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadDocuments = async (files: FileList) => {
    if (!currentSession) return;

    setIsLoading(true);
    try {
      await api.uploadDocuments(userId, currentSession.session_id, files);
      await loadSession(currentSession.session_id);
      await loadSessions();
      toast.success("Documents uploaded successfully");
    } catch (error) {
      toast.error("Failed to upload documents");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateNotes = async () => {
    if (!currentSession) return;

    setIsLoading(true);
    try {
      const response = await api.generateNotes(userId, currentSession.session_id);
      const downloadUrl = api.getDownloadUrl(response.pdf_filename);
      window.open(downloadUrl, "_blank");
      toast.success("Notes generated! Download started.");
    } catch (error) {
      toast.error("Failed to generate notes");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGeneratePracticeTest = async () => {
    if (!currentSession) return;

    setIsLoading(true);
    try {
      const response = await api.generatePracticeTest(userId, currentSession.session_id);
      const downloadUrl = api.getDownloadUrl(response.pdf_filename);
      window.open(downloadUrl, "_blank");
      toast.success("Practice test generated! Download started.");
    } catch (error) {
      toast.error("Failed to generate practice test");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isInitializing) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-background">
      <div className="w-80 flex-shrink-0">
        <SessionList
          sessions={sessions}
          currentSessionId={currentSession?.session_id || null}
          onSelectSession={loadSession}
          onCreateSession={handleCreateSession}
          onDeleteSession={handleDeleteSession}
        />
      </div>
      <div className="flex-1">
        {currentSession ? (
          <ChatInterface
            messages={currentSession.chat_history || []}
            documents={currentSession.documents}
            onSendMessage={handleSendMessage}
            onUploadDocuments={handleUploadDocuments}
            onGenerateNotes={handleGenerateNotes}
            onGeneratePracticeTest={handleGeneratePracticeTest}
            isLoading={isLoading}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">Welcome to Study Helper</h2>
              <p>Create a new session to get started</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;
