import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/services/api";
import type {
  BookmarkItem,
  BookmarkItemType,
  BookmarkListResponse,
} from "@/types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

const bookmarkQueryKey = (userId: string) => ["bookmarks", userId] as const;

function mergeBookmark(
  base: BookmarkListResponse,
  optimisticItem: BookmarkItem,
): BookmarkListResponse {
  const exists = base.bookmarks.some(
    (item) =>
      item.item_id === optimisticItem.item_id &&
      item.item_type === optimisticItem.item_type,
  );
  if (exists) return base;

  const bookmarks = [optimisticItem, ...base.bookmarks];
  return {
    bookmarks,
    pagination: {
      ...base.pagination,
      total: base.pagination.total + 1,
      has_more: false,
    },
  };
}

function removeBookmark(
  base: BookmarkListResponse,
  itemId: string,
  itemType: BookmarkItemType,
): BookmarkListResponse {
  const bookmarks = base.bookmarks.filter(
    (item) => !(item.item_id === itemId && item.item_type === itemType),
  );
  return {
    bookmarks,
    pagination: {
      ...base.pagination,
      total: Math.max(0, bookmarks.length),
      has_more: false,
    },
  };
}

export const useFavorites = () => {
  const queryClient = useQueryClient();
  const { user, token, isLoading: isAuthLoading } = useAuth();
  const userId = user?.id || "";

  const query = useQuery({
    queryKey: bookmarkQueryKey(userId),
    queryFn: () => apiClient.getBookmarks({ limit: 100, offset: 0 }),
    enabled: Boolean(userId && token),
  });

  const favorites = query.data?.bookmarks ?? [];

  const addMutation = useMutation({
    mutationFn: (payload: { itemId: string; itemType: BookmarkItemType }) =>
      apiClient.addBookmark({
        item_type: payload.itemType,
        item_id: payload.itemId,
      }),
    onMutate: async ({ itemId, itemType }) => {
      if (!userId)
        return { previous: undefined as BookmarkListResponse | undefined };
      await queryClient.cancelQueries({ queryKey: bookmarkQueryKey(userId) });
      const previous = queryClient.getQueryData<BookmarkListResponse>(
        bookmarkQueryKey(userId),
      );
      const optimisticItem: BookmarkItem = {
        item_id: itemId,
        item_type: itemType,
        scope_key: userId,
        created_at: new Date().toISOString(),
      };
      queryClient.setQueryData<BookmarkListResponse>(
        bookmarkQueryKey(userId),
        (current) =>
          mergeBookmark(
            current ?? {
              bookmarks: [],
              pagination: { total: 0, limit: 100, offset: 0, has_more: false },
            },
            optimisticItem,
          ),
      );
      return { previous };
    },
    onError: (_error, _variables, context) => {
      if (!userId) return;
      if (context?.previous) {
        queryClient.setQueryData(bookmarkQueryKey(userId), context.previous);
      }
    },
    onSettled: () => {
      if (!userId) return;
      queryClient.invalidateQueries({ queryKey: bookmarkQueryKey(userId) });
    },
  });

  const removeMutation = useMutation({
    mutationFn: (payload: { itemId: string; itemType: BookmarkItemType }) =>
      apiClient.removeBookmark(payload.itemType, payload.itemId),
    onMutate: async ({ itemId, itemType }) => {
      if (!userId)
        return { previous: undefined as BookmarkListResponse | undefined };
      await queryClient.cancelQueries({ queryKey: bookmarkQueryKey(userId) });
      const previous = queryClient.getQueryData<BookmarkListResponse>(
        bookmarkQueryKey(userId),
      );
      queryClient.setQueryData<BookmarkListResponse>(
        bookmarkQueryKey(userId),
        (current) =>
          current ? removeBookmark(current, itemId, itemType) : current,
      );
      return { previous };
    },
    onError: (_error, _variables, context) => {
      if (!userId) return;
      if (context?.previous) {
        queryClient.setQueryData(bookmarkQueryKey(userId), context.previous);
      }
    },
    onSettled: () => {
      if (!userId) return;
      queryClient.invalidateQueries({ queryKey: bookmarkQueryKey(userId) });
    },
  });

  const clearMutation = useMutation({
    mutationFn: (itemType?: BookmarkItemType) =>
      apiClient.clearBookmarks(itemType),
    onSuccess: () => {
      if (!userId) return;
      queryClient.setQueryData<BookmarkListResponse>(bookmarkQueryKey(userId), {
        bookmarks: [],
        pagination: { total: 0, limit: 100, offset: 0, has_more: false },
      });
    },
    onSettled: () => {
      if (!userId) return;
      queryClient.invalidateQueries({ queryKey: bookmarkQueryKey(userId) });
    },
  });

  const isFavorite = (id: string, type: BookmarkItemType = "cluster") =>
    favorites.some((item) => item.item_id === id && item.item_type === type);

  const toggleFavorite = (id: string, type: BookmarkItemType = "cluster") => {
    if (isFavorite(id, type)) {
      removeMutation.mutate({ itemId: id, itemType: type });
      return;
    }
    addMutation.mutate({ itemId: id, itemType: type });
  };

  const getFavorites = (type?: BookmarkItemType) => {
    if (!type) return favorites;
    return favorites.filter((item) => item.item_type === type);
  };

  const isMutating =
    addMutation.isPending ||
    removeMutation.isPending ||
    clearMutation.isPending;
  const isReady = Boolean(userId && token);
  const itemCounts = useMemo(
    () => ({
      cluster: favorites.filter((item) => item.item_type === "cluster").length,
      idea: favorites.filter((item) => item.item_type === "idea").length,
    }),
    [favorites],
  );

  return {
    scopeKey: userId || "default",
    favorites,
    isFavorite,
    toggleFavorite,
    getFavorites,
    clearFavorites: (type?: BookmarkItemType) => clearMutation.mutate(type),
    refetch: query.refetch,
    itemCounts,
    isReady,
    isLoading: isAuthLoading || (isReady ? query.isLoading : false),
    isFetching: query.isFetching,
    error: query.error,
    isMutating,
  };
};
