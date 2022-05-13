import { Run } from "./Models";

export type RunListPayload = {
  current_page_url: string;
  next_page_url: string | undefined;
  limit: number;
  next_cursor: string | undefined;
  after_cursor_count: number;
  content: Array<Run>;
};
