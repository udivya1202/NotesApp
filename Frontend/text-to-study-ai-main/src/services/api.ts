const API_BASE_URL = "http://localhost:8080";

export const api = {
	async createSession(userId: string, sessionName: string) {
		const response = await fetch(`${API_BASE_URL}/sessions/create`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ user_id: userId, session_name: sessionName }),
		});
		if (!response.ok) throw new Error("Failed to create session");
		return response.json();
	},

	async getSessions(userId: string) {
		const response = await fetch(`${API_BASE_URL}/sessions/${userId}`);
		if (!response.ok) throw new Error("Failed to fetch sessions");
		return response.json();
	},

	async getSession(userId: string, sessionId: string) {
		const response = await fetch(
			`${API_BASE_URL}/sessions/${userId}/${sessionId}`,
		);
		if (!response.ok) throw new Error("Failed to fetch session");
		return response.json();
	},

	async updateSession(userId: string, sessionId: string, sessionName: string) {
		const response = await fetch(
			`${API_BASE_URL}/sessions/${userId}/${sessionId}`,
			{
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ session_name: sessionName }),
			},
		);
		if (!response.ok) throw new Error("Failed to update session");
		return response.json();
	},

	async deleteSession(userId: string, sessionId: string) {
		const response = await fetch(
			`${API_BASE_URL}/sessions/${userId}/${sessionId}`,
			{
				method: "DELETE",
			},
		);
		if (!response.ok) throw new Error("Failed to delete session");
		return response.json();
	},

	async uploadDocuments(userId: string, sessionId: string, files: FileList) {
		const formData = new FormData();
		formData.append("user_id", userId);
		formData.append("session_id", sessionId);
		Array.from(files).forEach((file) => {
			formData.append("files", file);
		});

		const response = await fetch(`${API_BASE_URL}/upload`, {
			method: "POST",
			body: formData,
		});
		if (!response.ok) throw new Error("Failed to upload documents");
		return response.json();
	},

	async sendMessage(userId: string, sessionId: string, question: string) {
		const response = await fetch(`${API_BASE_URL}/chat`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				user_id: userId,
				session_id: sessionId,
				question,
			}),
		});
		if (!response.ok) throw new Error("Failed to send message");
		return response.json();
	},

	async generateNotes(userId: string, sessionId: string) {
		const response = await fetch(`${API_BASE_URL}/generate-notes`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ user_id: userId, session_id: sessionId }),
		});
		if (!response.ok) throw new Error("Failed to generate notes");
		return response.json();
	},

	async generatePracticeTest(userId: string, sessionId: string) {
		const response = await fetch(`${API_BASE_URL}/generate-practice-test`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ user_id: userId, session_id: sessionId }),
		});
		if (!response.ok) throw new Error("Failed to generate practice test");
		return response.json();
	},

	getDownloadUrl(filename: string) {
		return `${API_BASE_URL}/download/${filename}`;
	},
};
