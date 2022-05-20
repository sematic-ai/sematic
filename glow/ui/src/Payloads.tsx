import { Run } from "./Models";

export type RunListPayload = {
  current_page_url: string;
  next_page_url?: string;
  limit: number;
  next_cursor?: string;
  after_cursor_count: number;
  content: Array<Run>;
};

export type RunViewPayload = {
  content: Run;
};
