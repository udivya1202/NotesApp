import { Plus, Trash2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Session } from "@/types";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SessionListProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (sessionId: string) => void;
}

export const SessionList = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
}: SessionListProps) => {
  return (
    <div className="h-full flex flex-col border-r border-border bg-card">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold mb-3">Chat Sessions</h2>
        <Button onClick={onCreateSession} className="w-full" size="sm">
          <Plus className="h-4 w-4 mr-2" />
          New Session
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sessions.map((session) => (
            <div
              key={session.session_id}
              className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                currentSessionId === session.session_id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
              onClick={() => onSelectSession(session.session_id)}
            >
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <MessageSquare className="h-4 w-4 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{session.session_name}</p>
                  <p className="text-xs opacity-70">
                    {session.message_count} messages · {session.documents.length} docs
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="opacity-0 group-hover:opacity-100 h-8 w-8 flex-shrink-0"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.session_id);
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};
