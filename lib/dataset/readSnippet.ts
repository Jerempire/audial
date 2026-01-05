/**
 * Safely reads a code snippet from a song file.
 * Falls back to index snippet if file not readable.
 * Dataset has been removed - returns snippet from entry.
 */

import { SongIndexEntry } from "./types";

/**
 * Reads a snippet from a file, with fallback to index snippet.
 */
export function readSnippet(entry: SongIndexEntry): string {
  // Dataset has been removed - return snippet from entry
  return entry.snippet;
}

