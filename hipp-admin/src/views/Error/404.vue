<script setup lang="ts">
import { Error } from '@/components/Error'
import { BaseButton } from '@/components/Button'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'
import { useI18n } from '@/hooks/web/useI18n'

const { push } = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()

const errorClick = () => {
  push('/')
}

const handleLogout = () => {
  authStore.logout()
}
</script>

<template>
  <div class="flex flex-col items-center">
    <Error @error-click="errorClick" />
    <div v-if="authStore.getToken" class="mt-16px">
      <BaseButton @click="handleLogout">{{ t('common.loginOut') }}</BaseButton>
    </div>
  </div>
</template>
