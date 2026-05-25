import { defineStore } from 'pinia'
import { useAuthStore } from './auth'

export interface Block {
  id: string
  block_type: string
  sort_order: number
  is_visible: boolean
  config: Record<string, unknown>
}

export interface Profile {
  id: string
  slug: string
  status: 'draft' | 'published' | 'private'
  display_name: string
  bio: string | null
  tags: string[]
  blocks: Block[]
  theme_preset: string
  theme_tokens: Record<string, unknown> | null
  accent_color: string | null
  avatar_url: string | null
}

export const useProfileStore = defineStore('profile', {
  state: () => ({
    profile: null as Profile | null,
    loading: false,
  }),

  getters: {
    hasProfile: (state) => !!state.profile,
    isPublished: (state) => state.profile?.status === 'published',
  },

  actions: {
    async fetch() {
      const config = useRuntimeConfig()
      const auth = useAuthStore()
      this.loading = true
      try {
        this.profile = await auth.authorizedFetch<Profile>(`${config.public.apiBase}/profiles/me`)
      } catch (e: unknown) {
        const err = e as { status?: number; statusCode?: number }
        const status = err?.status ?? err?.statusCode
        if (status === 404) this.profile = null
        else throw e
      } finally {
        this.loading = false
      }
    },

    async create(data: { slug: string; display_name: string; bio?: string; tags?: string[] }) {
      const config = useRuntimeConfig()
      const auth = useAuthStore()
      this.profile = await auth.authorizedFetch<Profile>(`${config.public.apiBase}/profiles`, {
        method: 'POST',
        body: data,
      })
    },

    async update(data: Partial<{ slug: string; status: string; display_name: string; bio: string | null; tags: string[]; theme_preset: string; theme_tokens: Record<string, unknown> | null; accent_color: string | null }>) {
      const config = useRuntimeConfig()
      const auth = useAuthStore()
      this.profile = await auth.authorizedFetch<Profile>(`${config.public.apiBase}/profiles/me`, {
        method: 'PATCH',
        body: data,
      })
    },

    async createBlock(block_type: string, blockConfig: Record<string, unknown> = {}) {
      const config = useRuntimeConfig()
      const auth = useAuthStore()
      const block = await auth.authorizedFetch<Block>(`${config.public.apiBase}/profiles/me/blocks`, {
        method: 'POST',
        body: { block_type, config: blockConfig },
      })
      if (this.profile) {
        this.profile.blocks = [...this.profile.blocks, block]
      }
      return block
    },

    async updateBlock(id: string, data: { config?: Record<string, unknown>; is_visible?: boolean }) {
      const config = useRuntimeConfig()
      const auth = useAuthStore()
      const block = await auth.authorizedFetch<Block>(`${config.public.apiBase}/profiles/me/blocks/${id}`, {
        method: 'PATCH',
        body: data,
      })
      if (this.profile) {
        const idx = this.profile.blocks.findIndex(b => b.id === id)
        if (idx !== -1) {
          this.profile.blocks[idx] = block
          this.profile.blocks = [...this.profile.blocks]
        }
      }
      return block
    },

    async deleteBlock(id: string) {
      const config = useRuntimeConfig()
      const auth = useAuthStore()
      await auth.authorizedFetch(`${config.public.apiBase}/profiles/me/blocks/${id}`, {
        method: 'DELETE',
      })
      if (this.profile) {
        this.profile.blocks = this.profile.blocks.filter(b => b.id !== id)
      }
    },

    async reorder(ids: string[]) {
      const config = useRuntimeConfig()
      const auth = useAuthStore()
      await auth.authorizedFetch(`${config.public.apiBase}/profiles/me/blocks/reorder`, {
        method: 'PUT',
        body: { ids },
      })
      if (this.profile) {
        this.profile.blocks = [...this.profile.blocks].sort((a, b) => {
          return ids.indexOf(a.id) - ids.indexOf(b.id)
        })
      }
    },
  },
})
