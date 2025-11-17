// Vitest setup file for global test configuration
import '@testing-library/jest-dom';

// Mock DragEvent for jsdom environment
if (typeof global.DragEvent === 'undefined') {
  // Create a proper DragEvent class that extends Event
  global.DragEvent = class DragEvent extends Event {
    dataTransfer: DataTransfer;
    constructor(type: string, init?: DragEventInit) {
      super(type, { bubbles: init?.bubbles, cancelable: init?.cancelable });
      this.dataTransfer = init?.dataTransfer || new DataTransfer();
    }
  } as unknown as typeof DragEvent;

  // Also ensure window.DragEvent is available
  if (typeof window !== 'undefined') {
    (window as Window & { DragEvent?: typeof global.DragEvent }).DragEvent =
      global.DragEvent;
  }
}

// Mock DataTransfer if not available
if (typeof global.DataTransfer === 'undefined') {
  global.DataTransfer = class DataTransfer {
    items: DataTransferItemList;
    files: FileList;
    types: readonly string[];
    dropEffect: 'none' | 'copy' | 'link' | 'move';
    effectAllowed:
      | 'none'
      | 'copy'
      | 'copyLink'
      | 'copyMove'
      | 'link'
      | 'linkMove'
      | 'move'
      | 'all'
      | 'uninitialized';

    constructor() {
      this.items = [] as unknown as DataTransferItemList;
      this.files = [] as unknown as FileList;
      this.types = [];
      this.dropEffect = 'none';
      this.effectAllowed = 'all';
    }

    clearData(): void {}
    getData(): string {
      return '';
    }
    setData(): void {}
    setDragImage(): void {}
  } as unknown as typeof DataTransfer;
}
