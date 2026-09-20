import client from "./client";

export function getResumeFileUrl(resumeId) {
  return `${client.defaults.baseURL}/api/v1/resume/${resumeId}/file`;
}

export async function uploadResume(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await client.post("/api/v1/resume/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

export async function parseResume(resumeId) {
  const response = await client.post(`/api/v1/resume/${resumeId}/parse`);
  return response.data;
}

export async function indexResume(resumeId) {
  const response = await client.post(`/api/v1/resume/${resumeId}/index`);
  return response.data;
}