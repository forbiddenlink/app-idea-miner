// Favorites/Bookmarking System Hook
// Manages starred/bookmarked clusters with localStorage persistence

import { useState, useEffect } from "react";

interface FavoriteItem {
  id: string;
  type: "cluster" | "idea";
  timestamp: number;
}

export const useFavorites = () => {
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Load favorites from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem("app-idea-miner-favorites");
      if (stored) {
        setFavorites(JSON.parse(stored));
      }
      setError(null);
    } catch (e) {
      console.error("Failed to load favorites:", e);
      setError(e instanceof Error ? e : new Error("Failed to load favorites"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save to localStorage whenever favorites change
  useEffect(() => {
    localStorage.setItem("app-idea-miner-favorites", JSON.stringify(favorites));
  }, [favorites]);

  const toggleFavorite = (id: string, type: "cluster" | "idea" = "cluster") => {
    setIsMutating(true);
    setFavorites((prev) => {
      const exists = prev.find((f) => f.id === id && f.type === type);
      if (exists) {
        return prev.filter((f) => !(f.id === id && f.type === type));
      } else {
        return [...prev, { id, type, timestamp: Date.now() }];
      }
    });
    setIsMutating(false);
  };

  const isFavorite = (id: string, type: "cluster" | "idea" = "cluster") => {
    return favorites.some((f) => f.id === id && f.type === type);
  };

  const getFavorites = (type?: "cluster" | "idea") => {
    if (type) {
      return favorites.filter((f) => f.type === type);
    }
    return favorites;
  };

  const clearFavorites = (type?: "cluster" | "idea") => {
    setIsMutating(true);
    if (!type) {
      setFavorites([]);
    } else {
      setFavorites((prev) => prev.filter((f) => f.type !== type));
    }
    setIsMutating(false);
  };

  const itemCounts = {
    cluster: favorites.filter((f) => f.type === "cluster").length,
    idea: favorites.filter((f) => f.type === "idea").length,
  };

  return {
    favorites,
    toggleFavorite,
    isFavorite,
    getFavorites,
    clearFavorites,
    isLoading,
    isMutating,
    error,
    itemCounts,
  };
};
