// Vitest setup file for global test configuration
import '@testing-library/jest-dom';
import { beforeAll } from 'vitest';
import { JSDOM } from 'jsdom';

// Setup DOM globals for jsdom environment
beforeAll(() => {
  // Ensure global DOM objects are available
  if (typeof global.document === 'undefined') {
    const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
      url: 'http://localhost:3000',
      pretendToBeVisual: true,
      resources: 'usable',
    });

    global.document = dom.window.document;
    global.window = dom.window as any;
    global.navigator = dom.window.navigator;
    global.HTMLElement = dom.window.HTMLElement;
    global.Element = dom.window.Element;
  }
});

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
    (window as any).DragEvent = global.DragEvent;
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
