/**
 * UI状态管理（Zustand）
 *
 * 管理全局UI状态：主题、音乐源选择、匹配模式等
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { searchApi } from '../services/api';

// 默认音乐源（作为后备）
const FALLBACK_SOURCES = [
  'QQMusicClient',
  'NeteaseMusicClient',
  'KugouMusicClient',
  'KuwoMusicClient',
  'MiguMusicClient',
  'Pjmp3Client',
];

// 音乐源标签映射
const SOURCE_LABELS: Record<string, string> = {
  'QQMusicClient': 'QQ音乐',
  'NeteaseMusicClient': '网易云',
  'KugouMusicClient': '酷狗',
  'KuwoMusicClient': '酷我',
  'MiguMusicClient': '咪咕',
  'Pjmp3Client': 'pjmp3',
};

/**
 * 音乐源配置
 */
export interface SourceConfig {
  value: string;
  label: string;
}

/**
 * UI状态接口
 */
interface UIState {
  // 状态
  theme: 'light' | 'dark';
  selectedSources: string[];
  availableSources: SourceConfig[];  // 从 API 获取的可用音乐源
  sourcesLoaded: boolean;  // 音乐源是否已加载
  matchMode: 'strict' | 'standard' | 'loose';

  // Actions
  toggleSource: (source: string) => void;
  setSelectedSources: (sources: string[]) => void;
  setMatchMode: (mode: UIState['matchMode']) => void;
  resetSources: () => void;
  fetchSources: () => Promise<void>;  // 从 API 获取音乐源
}

/**
 * UI状态Store
 */
export const useUIStore = create<UIState>()(
  devtools(
    (set, get) => ({
      // 初始状态 - 默认使用宽松模式以提高匹配率
      theme: 'light',
      selectedSources: FALLBACK_SOURCES,  // 使用后备默认值
      availableSources: FALLBACK_SOURCES.map(s => ({
        value: s,
        label: SOURCE_LABELS[s] || s,
      })),
      sourcesLoaded: false,
      matchMode: 'loose',  // 默认使用宽松模式（0.3阈值），与后端保持一致

      // 切换音乐源选择
      toggleSource: (source: string) =>
        set((state) => ({
          selectedSources: state.selectedSources.includes(source)
            ? state.selectedSources.filter((s) => s !== source)
            : [...state.selectedSources, source],
        })),

      // 设置音乐源列表
      setSelectedSources: (sources: string[]) => set({ selectedSources: sources }),

      // 设置匹配模式
      setMatchMode: (mode: UIState['matchMode']) => set({ matchMode: mode }),

      // 重置为所有音乐源
      resetSources: () => set((state) => ({
        selectedSources: state.availableSources.map(s => s.value)
      })),

      // 从 API 获取音乐源
      fetchSources: async () => {
        try {
          const response = await searchApi.getSources();
          const sources = response.data.sources as SourceConfig[];

          if (sources && sources.length > 0) {
            set({
              availableSources: sources,
              sourcesLoaded: true,
              // 如果还没有选择任何源，默认全选
              selectedSources: get().selectedSources.length === 0
                ? sources.map(s => s.value)
                : get().selectedSources,
            });
          }
        } catch (error) {
          console.error('Failed to fetch sources:', error);
          // 保持使用后备默认值
          set({ sourcesLoaded: true });
        }
      },
    }),
    {
      name: 'UIStore',
    }
  )
);