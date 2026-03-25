import request from '@/config/axios'

export const getAgentListApi = (params: any): Promise<IResponse> => {
  return request.get({ url: '/vadmin/agent/agents', params })
}

export const addAgentApi = (data: any): Promise<IResponse> => {
  return request.post({ url: '/vadmin/agent/agents', data })
}

export const delAgentListApi = (data: any): Promise<IResponse> => {
  return request.delete({ url: '/vadmin/agent/agents', data })
}

export const putAgentApi = (data: any): Promise<IResponse> => {
  return request.put({ url: `/vadmin/agent/agents/${data.id}`, data })
}

export const getAgentApi = (dataId: number): Promise<IResponse> => {
  return request.get({ url: `/vadmin/agent/agents/${dataId}` })
}

/** 连通性测试：须传当前表单 api_server、app_key、remark；id 有值则后端更新该条并落库 */
export const testAgentApi = (data: {
  id?: number | null
  api_server: string
  app_key: string
  remark?: string | null
  service_type?: string | null
}): Promise<IResponse> => {
  return request.post({ url: '/vadmin/agent/agents/test', data })
}

export const publishAgentApi = (dataId: number): Promise<IResponse> => {
  return request.put({ url: `/vadmin/agent/agents/${dataId}/publish` })
}

export const unpublishAgentApi = (dataId: number): Promise<IResponse> => {
  return request.put({ url: `/vadmin/agent/agents/${dataId}/unpublish` })
}
