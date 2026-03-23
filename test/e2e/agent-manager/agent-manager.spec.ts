import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:9088'

test.describe('智能客服管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/agent/manager`)
  })

  test('F01 - 新增弹窗展示', async ({ page }) => {
    await page.click('button:has-text("新增智能客服")')
    const dialog = page.locator('.el-dialog')
    await expect(dialog).toBeVisible()
    await expect(dialog.locator('input').first()).toHaveValue('')
  })

  test('F02 - 填写并保存', async ({ page }) => {
    await page.click('button:has-text("新增智能客服")')
    const dialog = page.locator('.el-dialog')
    await dialog.locator('input').nth(0).fill('http://localhost/v1')
    await dialog.locator('input').nth(1).fill('test-key')
    await dialog.locator('input').nth(2).fill('测试备注')
    await dialog.locator('button:has-text("保存")').click()
  })

  test('F07 - 关键词搜索', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]')
    await searchInput.fill('客服')
    await page.keyboard.press('Enter')
    await page.waitForTimeout(500)
  })

  test('F08 - 状态下拉筛选', async ({ page }) => {
    const select = page.locator('.el-select').first()
    await select.click()
    const option = page.locator('.el-select-dropdown__item:has-text("已上架")')
    if (await option.isVisible()) {
      await option.click()
      await page.waitForTimeout(500)
    }
  })
})
