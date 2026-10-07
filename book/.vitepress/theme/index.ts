import DefaultTheme from 'vitepress/theme'
import './style.css'
import './northstar.css'
import { defineAsyncComponent } from 'vue'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('NorthstarLab', defineAsyncComponent(() => import('./components/NorthstarLab.vue')))
  }
}
