/**
 * Hand a blob to the browser as a download (the route is token-protected, so a plain link cannot fetch it).
 *
 * The anchor is attached while it is clicked and the object URL is released on the next turn of the event loop:
 * some browsers start the download asynchronously and would find the URL gone if it were revoked in the same tick.
 */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.style.display = 'none';
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
