export const getUserId = (): string => {
  let userId = localStorage.getItem('study_app_user_id');
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('study_app_user_id', userId);
  }
  return userId;
};

export const getCurrentSessionId = (): string | null => {
  return localStorage.getItem('study_app_current_session');
};

export const setCurrentSessionId = (sessionId: string) => {
  localStorage.setItem('study_app_current_session', sessionId);
};

export const clearCurrentSession = () => {
  localStorage.removeItem('study_app_current_session');
};
