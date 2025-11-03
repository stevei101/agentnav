// Vitest setup file for global test configuration

// Mock DataTransfer if not available (must be before DragEvent)
if (typeof global.DataTransfer === 'undefined') {
  global.DataTransfer = class DataTransfer {
    items: DataTransferItemList = [] as unknown as DataTransferItemList;
    files: FileList = [] as unknown as FileList;
    types: readonly string[] = [];
    dropEffect: 'none' | 'copy' | 'link' | 'move' = 'none';
    effectAllowed:
      | 'none'
      | 'copy'
      | 'copyLink'
      | 'copyMove'
      | 'link'
      | 'linkMove'
      | 'move'
      | 'all'
      | 'uninitialized' = 'all';

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

// Mock DragEvent for jsdom environment
if (typeof global.DragEvent === 'undefined') {
  global.DragEvent = class DragEvent extends Event {
    dataTransfer: DataTransfer;
    constructor(type: string, init?: DragEventInit) {
      super(type, init);
      this.dataTransfer = init?.dataTransfer || new DataTransfer();
    }
  } as unknown as typeof DragEvent;
}
