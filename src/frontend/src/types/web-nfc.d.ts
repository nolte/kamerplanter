// Web NFC API type declarations
// https://w3c.github.io/web-nfc/

interface NDEFMessage {
  records: readonly NDEFRecord[];
}

interface NDEFRecord {
  recordType: string;
  mediaType?: string;
  id?: string;
  data?: DataView | string;
  encoding?: string;
  lang?: string;
  toRecords?: () => NDEFRecord[];
}

interface NDEFWriteOptions {
  overwrite?: boolean;
  signal?: AbortSignal;
}

interface NDEFReadingEvent extends Event {
  serialNumber: string;
  message: NDEFMessage;
}

declare class NDEFReader {
  constructor();
  scan(options?: { signal?: AbortSignal }): Promise<void>;
  write(
    message: NDEFMessage | { records: Array<{ recordType: string; data?: string }> },
    options?: NDEFWriteOptions,
  ): Promise<void>;
  onreading: ((event: NDEFReadingEvent) => void) | null;
  onreadingerror: ((event: Event) => void) | null;
}

interface Window {
  NDEFReader?: typeof NDEFReader;
}
