import { api } from '../api/client'
import { useAction } from './useAction'

export const useAddEntry = () => useAction(api.addEntry)
export const useReplaceEntry = () => useAction(api.replaceEntry)
export const useSplitEntry = () => useAction(api.splitEntry)
export const useDeleteEntry = () => useAction(api.deleteEntry)
export const useAddCategory = () => useAction(api.addCategory)
export const useRenameCategory = () => useAction(api.renameCategory)
export const useDeleteCategory = () => useAction(api.deleteCategory)
export const useSetLimit = () => useAction(api.setLimit)
export const useDeleteLimit = () => useAction(api.deleteLimit)
