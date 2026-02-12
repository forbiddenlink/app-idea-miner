// Favorites/Bookmarking System Hook
// Manages starred/bookmarked clusters with localStorage persistence

import { useState, useEffect } from 'react';

interface FavoriteItem {
  id: string;
  type: 'cluster' | 'idea';
  timestamp: number;
}

export const useFavorites = () => {
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);

  // Load favorites from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('app-idea-miner-favorites');
    if (stored) {
      try {
        setFavorites(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to load favorites:', e);
      }
    }
  }, []);

  // Save to localStorage whenever favorites change
  useEffect(() => {
    localStorage.setItem('app-idea-miner-favorites', JSON.stringify(favorites));
  }, [favorites]);

  const toggleFavorite = (id: string, type: 'cluster' | 'idea' = 'cluster') => {
    setFavorites((prev) => {
      const exists = prev.find((f) => f.id === id && f.type === type);
      if (exists) {
        return prev.filter((f) => !(f.id === id && f.type === type));
      } else {
        return [...prev, { id, type, timestamp: Date.now() }];
      }
    });
  };

  const isFavorite = (id: string, type: 'cluster' | 'idea' = 'cluster') => {
    return favorites.some((f) => f.id === id && f.type === type);
  };

  const getFavorites = (type?: 'cluster' | 'idea') => {
    if (type) {
      return favorites.filter((f) => f.type === type);
    }
    return favorites;
  };

  const clearFavorites = () => {
    setFavorites([]);
  };

  return {
    favorites,
    toggleFavorite,
    isFavorite,
    getFavorites,
    clearFavorites,
  };
};
