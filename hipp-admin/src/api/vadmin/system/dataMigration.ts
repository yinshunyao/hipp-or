import request from '@/config/axios'

/** 导出业务数据 ZIP（需 responseType blob，自行处理下载与错误 JSON） */
export const postDataMigrationExportApi = () => {
  return request.post({
    url: '/vadmin/system/data-migration/export',
    responseType: 'blob'
  })
}

/** 导入业务数据 ZIP（全量替换） */
export const postDataMigrationImportApi = (data: FormData) => {
  return request.post({
    url: '/vadmin/system/data-migration/import',
    headersType: 'multipart/form-data',
    data
  })
}
