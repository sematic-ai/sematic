import { SidebarItemsType } from "../types/sidebar";

import {
  Box,
  Codesandbox,
  Type,
} from "react-feather";

const pagesSection = [
  {
    href: "/",
    icon: Codesandbox,
    title: "Discover",
  },
  {
    href: "/runs",
    icon: Box,
    title: "Runs",
  },
  {
    href: "/types",
    icon: Type,
    title: "Types",
  },
] as SidebarItemsType[];

const navItems = [
  {
    title: "Glow Workspace",
    pages: pagesSection,
  },
];

export default navItems;
