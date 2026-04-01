import { Document } from '../../shared/types/document';

export async function getDocuments(token: string): Promise<Document[]> {
  // Minimal stub: returns empty array
  return [];
}

export async function deleteDocument(documentId: string, token: string): Promise<void> {
  // Minimal stub: does nothing
  return;
}
