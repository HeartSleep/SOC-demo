import type { Component } from 'vue'
import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import type { User } from './index'

// Route types
export interface RouteConfig {
  path: string
  name?: string
  component?: Component | (() => Promise<Component>)
  redirect?: string
  alias?: string | string[]
  children?: RouteConfig[]
  meta?: RouteMeta
  beforeEnter?: NavigationGuard
  props?: boolean | Record<string, any> | ((route: RouteLocationNormalized) => Record<string, any>)
}

export interface RouteMeta {
  title?: string
  icon?: string
  requiresAuth?: boolean
  roles?: string[]
  permissions?: string[]
  hideInMenu?: boolean
  hideInBreadcrumb?: boolean
  keepAlive?: boolean
  affix?: boolean
  badge?: string | number | (() => string | number)
  activeMenu?: string
  noTagsView?: boolean
  followAuth?: boolean
  canTo?: boolean
  hidden?: boolean
}

export type NavigationGuard = (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => void

// Store types
export interface RootState {
  user: UserState
  app: AppState
  permission: PermissionState
  tagsView: TagsViewState
  settings: SettingsState
}

export interface UserState {
  token: string
  user: User | null
  roles: string[]
  permissions: string[]
  isLoggedIn: boolean
}

export interface AppState {
  device: 'desktop' | 'mobile'
  sidebar: {
    opened: boolean
    withoutAnimation: boolean
  }
  language: string
  size: 'large' | 'default' | 'small'
  theme: 'light' | 'dark' | 'auto'
}

export interface PermissionState {
  routes: RouteConfig[]
  addRoutes: RouteConfig[]
}

export interface TagsViewState {
  visitedViews: RouteView[]
  cachedViews: string[]
}

export interface RouteView {
  path: string
  name?: string
  title?: string
  fullPath: string
  params?: Record<string, string>
  query?: Record<string, any>
  meta?: RouteMeta
  affix?: boolean
}

export interface SettingsState {
  theme: string
  fixedHeader: boolean
  showLogo: boolean
  showTagsView: boolean
  showSettings: boolean
  sidebarTextTheme: boolean
  showFooter: boolean
  menuUniqueOpened: boolean
  menuCollapse: boolean
  layout: 'classic' | 'topLeft' | 'top' | 'cutMenu'
  isDrawer: boolean
}

// Component prop types
export interface TableColumn {
  prop?: string
  label: string
  width?: string | number
  minWidth?: string | number
  fixed?: boolean | 'left' | 'right'
  sortable?: boolean | 'custom'
  align?: 'left' | 'center' | 'right'
  headerAlign?: 'left' | 'center' | 'right'
  showOverflowTooltip?: boolean
  type?: 'selection' | 'index' | 'expand'
  formatter?: (row: any, column: any, cellValue: any, index: number) => any
  className?: string
  labelClassName?: string
  selectable?: (row: any, index: number) => boolean
  reserveSelection?: boolean
  filters?: Array<{ text: string; value: any }>
  filterMethod?: (value: any, row: any, column: any) => boolean
  render?: (row: any, column: any, cellValue: any, index: number) => any
}

export interface TableProps {
  data: any[]
  columns: TableColumn[]
  loading?: boolean
  border?: boolean
  stripe?: boolean
  size?: 'large' | 'default' | 'small'
  fit?: boolean
  showHeader?: boolean
  highlightCurrentRow?: boolean
  currentRowKey?: string | number
  rowClassName?: string | ((row: any, rowIndex: number) => string)
  rowStyle?: Record<string, any> | ((row: any, rowIndex: number) => Record<string, any>)
  cellClassName?: string | ((row: any, column: any, rowIndex: number, columnIndex: number) => string)
  cellStyle?: Record<string, any> | ((row: any, column: any, rowIndex: number, columnIndex: number) => Record<string, any>)
  headerRowClassName?: string | ((row: any, rowIndex: number) => string)
  headerRowStyle?: Record<string, any> | ((row: any, rowIndex: number) => Record<string, any>)
  headerCellClassName?: string | ((row: any, column: any, rowIndex: number, columnIndex: number) => string)
  headerCellStyle?: Record<string, any> | ((row: any, column: any, rowIndex: number, columnIndex: number) => Record<string, any>)
  rowKey?: string | ((row: any) => string)
  emptyText?: string
  defaultExpandAll?: boolean
  expandRowKeys?: (string | number)[]
  defaultSort?: { prop: string; order: 'ascending' | 'descending' }
  tooltipEffect?: 'dark' | 'light'
  showSummary?: boolean
  sumText?: string
  summaryMethod?: (columns: any[], data: any[]) => string[]
  spanMethod?: (row: any, column: any, rowIndex: number, columnIndex: number) => number[] | { rowspan: number; colspan: number }
  selectOnIndeterminate?: boolean
  indent?: number
  lazy?: boolean
  load?: (row: any, treeNode: any, resolve: (data: any[]) => void) => void
  treeProps?: { children?: string; hasChildren?: string }
}

export interface FormItem {
  prop?: string
  label?: string
  labelWidth?: string | number
  required?: boolean
  rules?: any[]
  error?: string
  showMessage?: boolean
  inlineMessage?: boolean
  size?: 'large' | 'default' | 'small'
  for?: string
}

export interface FormProps {
  model: Record<string, any>
  rules?: Record<string, any[]>
  inline?: boolean
  labelPosition?: 'left' | 'right' | 'top'
  labelWidth?: string | number
  labelSuffix?: string
  hideRequiredAsterisk?: boolean
  showMessage?: boolean
  inlineMessage?: boolean
  statusIcon?: boolean
  validateOnRuleChange?: boolean
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
}

// Dialog types
export interface DialogProps {
  modelValue: boolean
  title?: string
  width?: string | number
  fullscreen?: boolean
  top?: string
  modal?: boolean
  modalAppendToBody?: boolean
  appendToBody?: boolean
  lockScroll?: boolean
  customClass?: string
  openDelay?: number
  closeDelay?: number
  closeOnClickModal?: boolean
  closeOnPressEscape?: boolean
  showClose?: boolean
  beforeClose?: (done: () => void) => void
  draggable?: boolean
  center?: boolean
  alignCenter?: boolean
  destroyOnClose?: boolean
}

// Loading types
export interface LoadingProps {
  target?: string | HTMLElement
  body?: boolean
  fullscreen?: boolean
  lock?: boolean
  text?: string
  spinner?: string
  background?: string
  customClass?: string
}

// Message types
export interface MessageOptions {
  message: string | Component
  type?: 'success' | 'warning' | 'info' | 'error'
  iconClass?: string
  dangerouslyUseHTMLString?: boolean
  customClass?: string
  duration?: number
  showClose?: boolean
  center?: boolean
  onClose?: () => void
  offset?: number
  appendTo?: string | HTMLElement
}

// Notification types
export interface NotificationOptions {
  title?: string
  message?: string | Component
  type?: 'success' | 'warning' | 'info' | 'error'
  iconClass?: string
  customClass?: string
  duration?: number
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
  showClose?: boolean
  onClose?: () => void
  onClick?: () => void
  offset?: number
}

// Upload types
export interface UploadFile {
  name: string
  percentage?: number
  status?: 'ready' | 'uploading' | 'success' | 'fail'
  size?: number
  response?: any
  uid?: number
  url?: string
  raw?: File
}

export interface UploadProps {
  action: string
  headers?: Record<string, any>
  method?: string
  multiple?: boolean
  data?: Record<string, any>
  name?: string
  withCredentials?: boolean
  showFileList?: boolean
  drag?: boolean
  accept?: string
  onPreview?: (file: UploadFile) => void
  onRemove?: (file: UploadFile, fileList: UploadFile[]) => void
  onSuccess?: (response: any, file: UploadFile, fileList: UploadFile[]) => void
  onError?: (err: any, file: UploadFile, fileList: UploadFile[]) => void
  onProgress?: (event: any, file: UploadFile, fileList: UploadFile[]) => void
  onChange?: (file: UploadFile, fileList: UploadFile[]) => void
  onExceed?: (files: File[], fileList: UploadFile[]) => void
  beforeUpload?: (file: File) => boolean | Promise<File>
  beforeRemove?: (file: UploadFile, fileList: UploadFile[]) => boolean | Promise<any>
  listType?: 'text' | 'picture' | 'picture-card'
  autoUpload?: boolean
  fileList?: UploadFile[]
  httpRequest?: (options: any) => any
  disabled?: boolean
  limit?: number
}

// Chart types
export interface ChartOptions {
  title?: {
    text?: string
    subtext?: string
    left?: string | number
    top?: string | number
    right?: string | number
    bottom?: string | number
    textStyle?: Record<string, any>
    subtextStyle?: Record<string, any>
  }
  tooltip?: {
    show?: boolean
    trigger?: 'item' | 'axis' | 'none'
    formatter?: string | Function
    backgroundColor?: string
    borderColor?: string
    borderWidth?: number
    textStyle?: Record<string, any>
  }
  legend?: {
    show?: boolean
    type?: 'plain' | 'scroll'
    orient?: 'horizontal' | 'vertical'
    left?: string | number
    top?: string | number
    right?: string | number
    bottom?: string | number
    data?: string[]
    textStyle?: Record<string, any>
  }
  grid?: {
    show?: boolean
    left?: string | number
    top?: string | number
    right?: string | number
    bottom?: string | number
    width?: string | number
    height?: string | number
    containLabel?: boolean
  }
  xAxis?: {
    type?: 'category' | 'value' | 'time' | 'log'
    name?: string
    nameLocation?: 'start' | 'middle' | 'end'
    nameTextStyle?: Record<string, any>
    data?: any[]
    axisLine?: Record<string, any>
    axisTick?: Record<string, any>
    axisLabel?: Record<string, any>
    splitLine?: Record<string, any>
  }
  yAxis?: {
    type?: 'category' | 'value' | 'time' | 'log'
    name?: string
    nameLocation?: 'start' | 'middle' | 'end'
    nameTextStyle?: Record<string, any>
    data?: any[]
    axisLine?: Record<string, any>
    axisTick?: Record<string, any>
    axisLabel?: Record<string, any>
    splitLine?: Record<string, any>
  }
  series?: {
    name?: string
    type?: 'line' | 'bar' | 'pie' | 'scatter' | 'radar' | 'gauge'
    data?: any[]
    itemStyle?: Record<string, any>
    lineStyle?: Record<string, any>
    areaStyle?: Record<string, any>
    smooth?: boolean
    stack?: string
    radius?: string | string[]
    center?: string[]
    roseType?: 'radius' | 'area'
    label?: Record<string, any>
    labelLine?: Record<string, any>
    emphasis?: Record<string, any>
  }[]
  color?: string[]
  backgroundColor?: string
  textStyle?: Record<string, any>
  animation?: boolean
  animationDuration?: number
  animationEasing?: string
}

// Menu types
export interface MenuOption {
  key: string
  label: string
  icon?: string
  disabled?: boolean
  children?: MenuOption[]
  meta?: Record<string, any>
}

// Breadcrumb types
export interface BreadcrumbItem {
  title: string
  path?: string
  disabled?: boolean
  icon?: string
}

// Pagination types
export interface PaginationConfig {
  page: number
  size: number
  total: number
  sizes?: number[]
  layout?: string
  pageSizes?: number[]
  pagerCount?: number
  currentPage?: number
  pageSize?: number
  background?: boolean
  small?: boolean
  hideOnSinglePage?: boolean
}

// Tree types
export interface TreeNode {
  id: string | number
  label: string
  children?: TreeNode[]
  disabled?: boolean
  isLeaf?: boolean
  [key: string]: any
}

export interface TreeProps {
  data: TreeNode[]
  emptyText?: string
  nodeKey?: string
  props?: {
    label?: string
    children?: string
    disabled?: string
    isLeaf?: string
  }
  renderAfterExpand?: boolean
  load?: (node: any, resolve: (data: TreeNode[]) => void) => void
  renderContent?: (h: Function, data: { node: any, data: TreeNode, store: any }) => any
  highlightCurrent?: boolean
  defaultExpandAll?: boolean
  expandOnClickNode?: boolean
  checkOnClickNode?: boolean
  autoExpandParent?: boolean
  defaultExpandedKeys?: (string | number)[]
  showCheckbox?: boolean
  checkStrictly?: boolean
  defaultCheckedKeys?: (string | number)[]
  currentNodeKey?: string | number
  filterNodeMethod?: (value: any, data: TreeNode, node: any) => boolean
  accordion?: boolean
  indent?: number
  iconClass?: string
  lazy?: boolean
  draggable?: boolean
  allowDrag?: (node: any) => boolean
  allowDrop?: (draggingNode: any, dropNode: any, type: 'prev' | 'inner' | 'next') => boolean
}

// Date picker types
export interface DatePickerShortcut {
  text: string
  value: Date | (() => Date | Date[])
}

// Transfer types
export interface TransferData {
  key: string | number
  label: string
  disabled?: boolean
}

// Cascader types
export interface CascaderOption {
  value: string | number
  label: string
  children?: CascaderOption[]
  disabled?: boolean
  leaf?: boolean
}

// Color picker types
export interface ColorFormat {
  format?: 'hsl' | 'hsv' | 'hex' | 'rgb'
  alpha?: boolean
}

// Rate types
export interface RateColors {
  [key: number]: string
}

// Slider types
export interface SliderMarks {
  [key: number]: string | { style: Record<string, any>; label: string }
}