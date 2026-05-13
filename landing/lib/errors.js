/** 用户友好错误消息映射 */

const ERROR_MESSAGES = {
  'Failed to fetch': '无法连接服务器，请检查网络或稍后重试',
  'NetworkError': '网络异常，请检查连接后重试',
  'NetworkError when attempting to fetch resource.': '网络异常，请检查连接后重试',
  'The user aborted a request.': '请求超时，请重试',
  'Load failed': '加载失败，请检查网络',
  'TypeError: Failed to fetch': '无法连接服务器',
  '登录已过期': '登录已过期，请重新登录',
  'Token 无效或已过期': '登录已过期，请重新登录',
  '未登录': '请先登录',
  '用户名或密码错误': '用户名或密码错误',
  '用户名已存在': '该用户名已被注册',
  '密码至少 6 位': '密码至少需要6位字符',
  '用户名仅限英文、数字、下划线': '用户名只能包含英文、数字和下划线',
  '此功能仅限专业版（Pro）用户使用': '此功能需升级专业版使用',
  '免费版每月限上传 20 个文件': '免费版每月限上传20个文件，升级专业版可解除限制',
  '免费版最多保存 200 个产品': '免费版最多保存200个产品，升级专业版可解除限制',
  '产品列表不能为空': '请先添加产品',
  '每个产品必须包含型号（model）': '每个产品必须填写型号',
  '仅支持 .xlsx / .xls / .pdf / .docx 格式': '仅支持 Excel(.xlsx/.xls)、PDF、Word(.docx) 格式',
  '解析失败': '文件解析失败，请检查文件格式是否正确',
  'No products found in file': '文件中未找到产品数据',
  'AI 无法识别此文件格式': 'AI 无法识别此文件格式，请使用标准解析',
  'AI 解析后未找到产品数据': 'AI 解析未找到产品数据',
  'AI 解析暂不支持 PDF/DOCX 格式': 'AI 解析暂不支持 PDF/Word 格式',
  生成失败: '文档生成失败，请重试',
  'PI generation failed': '形式发票生成失败',
  'Packing list generation failed': '装箱单生成失败',
  'Invoice generation failed': '商业发票生成失败',
  'PDF generation failed': 'PDF 生成失败，请重试',
  '文件超过 50MB 限制': '文件超过50MB限制',
  '图片未找到': '图片未找到',
  '获取失败': '获取数据失败，请刷新重试',
};

/**
 * 将 API 错误转为用户友好的中文消息
 * @param {Error|string} err - 错误对象或消息字符串
 * @returns {string} 用户友好的中文错误消息
 */
export function friendlyError(err) {
  if (!err) return '未知错误';
  const msg = typeof err === 'string' ? err : (err.message || err.detail || '');
  return ERROR_MESSAGES[msg] || ERROR_MESSAGES[msg.trim()] || msg || '操作失败，请重试';
}

/**
 * 友好的 alert 包装
 */
export function alertError(err) {
  alert(friendlyError(err));
}
