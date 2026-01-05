/**
 * Type definitions for the dataset (local copy)
 */

export interface SongIndexEntry {
  id: string;
  title: string;
  author?: string;
  source_path: string;
  snippet: string;
  slug?: string;
  title_tokens?: string[];
  path_tokens?: string[];
  aliases?: string[];
  genres: string[];
  moods: string[];
  techniques: string[];
  instruments: string[];
  bpm?: number;
  prompt_seeds: string[];
}

export interface SongIndex {
  songs: SongIndexEntry[];
  version: string;
  generated_at: string;
}

export interface StylePriors {
  summary_bullets: string[];
  version: string;
  generated_at: string;
}

