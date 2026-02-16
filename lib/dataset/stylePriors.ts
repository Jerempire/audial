/**
 * Loads style priors from the dataset.
 * Reads from data/style-priors.json (bundled at build time).
 */

import { StylePriors } from "./schema";
import priorData from "../../data/style-priors.json";

let cached: StylePriors | null = null;

export function loadStylePriors(): StylePriors | null {
  if (!cached && priorData?.summary_bullets?.length > 0) {
    cached = priorData as StylePriors;
  }
  return cached;
}

export function getStylePriors(): StylePriors | null {
  return loadStylePriors();
}
