import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

export interface AccessibilityOptions {
  announceChanges?: boolean;
  focusManagement?: boolean;
  keyboardNavigation?: boolean;
}

export const useAccessibility = (options: AccessibilityOptions = {}) => {
  const {
    announceChanges = true,
    focusManagement = true,
    keyboardNavigation = true,
  } = options;

  const announceToScreenReader = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!announceChanges) return;

    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Clean up after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, [announceChanges]);

  const focusElement = useCallback((selector: string) => {
    if (!focusManagement) return;

    const element = document.querySelector(selector) as HTMLElement;
    if (element) {
      element.focus();
    }
  }, [focusManagement]);

  const trapFocus = useCallback((container: HTMLElement) => {
    if (!focusManagement) return;

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    
    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  }, [focusManagement]);

  const handleKeyboardNavigation = useCallback((onEscape?: () => void) => {
    if (!keyboardNavigation) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && onEscape) {
        onEscape();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [keyboardNavigation]);

  return {
    announceToScreenReader,
    focusElement,
    trapFocus,
    handleKeyboardNavigation,
  };
};

export const useKeyboardShortcuts = () => {
  const { t } = useTranslation();

  const shortcuts = {
    'ctrl+u': t('keyboard.uploadFile'),
    'ctrl+n': t('keyboard.newAnalysis'),
    'ctrl+f': t('keyboard.search'),
    'escape': t('keyboard.escape'),
    'f1': t('keyboard.help'),
  };

  const handleShortcut = useCallback((callback: () => void, keys: string[]) => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const pressedKeys = [];
      
      if (e.ctrlKey) pressedKeys.push('ctrl');
      if (e.shiftKey) pressedKeys.push('shift');
      if (e.altKey) pressedKeys.push('alt');
      if (e.metaKey) pressedKeys.push('meta');
      
      const key = e.key.toLowerCase();
      pressedKeys.push(key);
      
      const shortcut = pressedKeys.join('+');
      
      if (keys.includes(shortcut)) {
        e.preventDefault();
        callback();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return {
    shortcuts,
    handleShortcut,
  };
};

export const useFocusManagement = () => {
  const { focusElement } = useAccessibility();

  const focusUploadArea = useCallback(() => {
    focusElement('#file-upload');
  }, [focusElement]);

  const focusSearch = useCallback(() => {
    focusElement('input[placeholder*="Search"]');
  }, [focusElement]);

  const focusNewAnalysis = useCallback(() => {
    focusElement('button:has-text("New Analysis")');
  }, [focusElement]);

  return {
    focusUploadArea,
    focusSearch,
    focusNewAnalysis,
  };
};
