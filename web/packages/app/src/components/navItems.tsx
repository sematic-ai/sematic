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
    title: "Glow",
    pages: pagesSection,
  },
];

export default navItems;
