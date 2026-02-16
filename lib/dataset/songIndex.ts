/**
 * Loads and provides access to the song index.
 * Reads from data/song-index.json (bundled at build time).
 */

import { SongIndex } from "./schema";
import songData from "../../data/song-index.json";

let cached: SongIndex | null = null;

export function loadSongIndex(): SongIndex | null {
  if (!cached && songData?.songs?.length > 0) {
    cached = songData as SongIndex;
  }
  return cached;
}

export function getSongIndex(): SongIndex | null {
  return loadSongIndex();
}
