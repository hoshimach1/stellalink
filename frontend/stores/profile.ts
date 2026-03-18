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
    _headers() {
      const auth = useAuthStore()
      return { Authorization: `Bearer ${auth.accessToken}` }
    },

    async fetch() {
      const config = useRuntimeConfig()
      this.loading = true
      try {
        this.profile = await $fetch<Profile>(`${config.public.apiBase}/profiles/me`, {
          headers: this._headers(),
        })
      } catch (e: unknown) {
        const err = e as { status?: number }
        if (err?.status === 404) this.profile = null
        else throw e
      } finally {
        this.loading = false
      }
    },

    async create(data: { slug: string; display_name: string; bio?: string; tags?: string[] }) {
      const config = useRuntimeConfig()
      this.profile = await $fetch<Profile>(`${config.public.apiBase}/profiles`, {
        method: 'POST',
        headers: this._headers(),
        body: data,
      })
    },

    async update(data: Partial<{ slug: string; status: string; display_name: string; bio: string; tags: string[] }>) {
      const config = useRuntimeConfig()
      this.profile = await $fetch<Profile>(`${config.public.apiBase}/profiles/me`, {
        method: 'PATCH',
        headers: this._headers(),
        body: data,
      })
    },

    async createBlock(block_type: string, blockConfig: Record<string, unknown> = {}) {
      const config = useRuntimeConfig()
      const block = await $fetch<Block>(`${config.public.apiBase}/profiles/me/blocks`, {
        method: 'POST',
        headers: this._headers(),
        body: { block_type, config: blockConfig },
      })
      this.profile?.blocks.push(block)
      return block
    },

    async updateBlock(id: string, data: { config?: Record<string, unknown>; is_visible?: boolean }) {
      const config = useRuntimeConfig()
      const block = await $fetch<Block>(`${config.public.apiBase}/profiles/me/blocks/${id}`, {
        method: 'PATCH',
        headers: this._headers(),
        body: data,
      })
      if (this.profile) {
        const idx = this.profile.blocks.findIndex(b => b.id === id)
        if (idx !== -1) this.profile.blocks[idx] = block
      }
      return block
    },

    async deleteBlock(id: string) {
      const config = useRuntimeConfig()
      await $fetch(`${config.public.apiBase}/profiles/me/blocks/${id}`, {
        method: 'DELETE',
        headers: this._headers(),
      })
      if (this.profile) {
        this.profile.blocks = this.profile.blocks.filter(b => b.id !== id)
      }
    },

    async reorder(ids: string[]) {
      const config = useRuntimeConfig()
      await $fetch(`${config.public.apiBase}/profiles/me/blocks/reorder`, {
        method: 'PUT',
        headers: this._headers(),
        body: { ids },
      })
    },
  },
})
