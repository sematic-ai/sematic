import { SidebarItemsType } from "../types/sidebar";

import {
  Box
} from "react-feather";

const pagesSection = [
  {
    href: "/",
    icon: Box,
    title: "Runs",
  },
] as SidebarItemsType[];

const navItems = [
  {
    title: "Glow Workspace",
    pages: pagesSection,
  },
];

export default navItems;
