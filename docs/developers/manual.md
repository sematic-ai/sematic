# Developer manual

## Getting started

## Dev Tools

```shell
$ make py-prep
```

## Add a third-party pip dependency

Add your dependency to `pyproject.toml`. Avoid pinning a fixed version unless necessary.

Then run (only supported on Linux):
```shell
$ make refresh-dependencies
```

## Activate virtual environment

```shell
$ source .venv/bin/activate
```

## Starting the API server

```shell
$ python -m sematic.api.server
```

## Starting the UI Dashboard

```shell
$ cd sematic/ui
$ npm start
```

The UI Dashboard is capable of hooking up with an alternative backend other than the local one. To do so, 
setting `SEMATIC_PROXY_OVERRIDE` environment variable to the URL of a backend deployment. All backend requests
issued from the dashboard are going to proxy to that address.

## Diagnose UI Dashboard issues

The local development server launched by [Create-React-Apps](https://create-react-app.dev/) is set up by default to provide extensive logging, which is helpful for investigating issues with the front-end. However, this logging is disabled by default for production builds.

If you need to enable excessive logging in a production build, you can add "debug=true" as a query parameter to any dashboard page (being careful not to add it after URL hashes). Once you've set this parameter, it will be remembered even if you don't explicitly include it in the URL. This means that the debug state will be maintained even after page refreshes.

To turn off excessive logging, you can append debug=false to the URL again, or you can clear it from localStorage using browser developer tools.

## Starting Storybook to browse UI components

```shell
$ cd sematic/ui
$ npm run storybook
```

## Plugin System in the Front End space
The FE plugin system extensively utilizes the functionality provided by  [react-slot-fill](https://github.com/camwest/react-slot-fill).

To comprehend the workings of the plugin system at a higher level, let's consider the example of RunTabs. In the case of RunTabs, we want plugins to dynamically add additional TabPanels in a decoupled manner.

To achieve this, we define a `<Slot>` within the `<TabContext>` in __RunTabs.tsx__:

```
<TabContext>
    <TabPanel value="input"/>
    <TabPanel value="output"/>
    ....
    <Slot name="run-tabs" />
</TabContext>
```
Next, in the __index.tsx__ file of the __main__ package, we render a `<PluginsLoader />` component:

```
<PluginsLoader />
```

The content of __PluginsLoader.tsx__ would be as follows:

```
import MyNewPlugin from "@sematic/addon-new-panel";

export default function PluginsLoader() {
    return <MyNewPlugin/>;
}
```

Finally, in `<MyNewPlugin/>`, we render a `<Fill>` component as follows:

```
function MyNewPlugin() {
    return <Fill name="run-tabs" >
        <TabPanel value="newPanel">
            <NewPanelImpl />
        </TabPanel>
    </Fill>
}
```

Whenever and wherever the `<MyNewPlugin />` component is rendered, its content within the `<Fill>` component will be attached to the `<Slot>` with the same name. This results in the expansion of panels rendered by RunTabs.tsx.

Both the `<Fill>` and `<Slot>` components can exist at different locations in the React Virtual DOM tree as long as they share a common ancestor node `<Provider>` from the [react-slot-fill](https://github.com/camwest/react-slot-fill) package. This implementation ensures decoupling, making it well-suited for the plugin system.

If, at a later stage, we need to remove the __MyNewPlugin__ component for any reason, we simply need to delete the entire __@sematic/addon-new-panel__ package and remove the reference from __PluginsLoader.tsx__.


## Building the Sematic Wheel

This is if you want to package a dev Sematic version for installation somewhere else:

```shell
$ make py-prep  # if not done before
$ make ui
$ make wheel
```
