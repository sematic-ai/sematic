export const parameters = {
  actions: { argTypesRegex: "^on[A-Z].*" },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
  toolbar: {
    icon: 'circlehollow',
    // Array of plain string values or MenuItem shape (see below)
    items: ['light', 'dark'],
    // Property that specifies if the name of the item will be displayed
    showName: true,
    // Change title based on selected value
    dynamicTitle: true,
  },
}