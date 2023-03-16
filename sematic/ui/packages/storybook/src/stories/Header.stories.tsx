import React from 'react';
import { Meta, StoryObj } from '@storybook/react';
import Menu from '@sematic/common/src/component/menu';

export default {
  title: 'Sematic/Header',
  component: Menu,

} as Meta<typeof Menu>;


export const Header: StoryObj<typeof Menu> = {
  render: () => {
    return <Menu />  
  }
};

