<script setup lang="ts">
import noPermission from '@/assets/svgs/403.svg'
import { BaseButton } from '@/components/Button'
import { useI18n } from '@/hooks/web/useI18n'
import { useAuthStore } from '@/store/modules/auth'

const { t } = useI18n()
const authStore = useAuthStore()

const onLogout = () => {
  authStore.logout()
}
</script>

<template>
  <div class="flex justify-center">
    <div class="text-center max-w-lg px-16px">
      <img width="350" :src="noPermission" alt="" />
      <div class="text-16px font-medium text-[var(--el-text-color-primary)] mt-8px">
        {{ t('error.noAccessTitle') }}
      </div>
      <p class="text-14px text-[var(--el-color-info)] leading-relaxed mt-12px">
        {{ t('error.noAccessDesc') }}
      </p>
      <div class="mt-24px">
        <BaseButton type="primary" size="large" @click="onLogout">
          {{ t('error.logoutToSwitch') }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>
