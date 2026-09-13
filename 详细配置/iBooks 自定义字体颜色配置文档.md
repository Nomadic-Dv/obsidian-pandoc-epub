
本文档记录在 EPUB 中嵌入自定义字体、并让特定文本颜色在 iBooks（Apple Books）日间/夜间模式下均能正常显示的完整方案。

---

## 一、背景与限制

iBooks 对普通文本的颜色有特殊处理：

- **默认情况下**，iBooks 会把字体和颜色控制权交给读者。
- 只有读者选择 **“原始字体”（Original）** 时，你写的 CSS 样式（包括颜色）才会生效。
- 读者一旦切换为系统字体（如苹方、宋体），iBooks 会**强制覆盖**你的所有颜色设置。
- 在**夜间模式**下，即使读者选了“原始字体”，iBooks 也会默认把文字强制变成白色，覆盖你的自定义颜色。

因此，要实现“日间和夜间都能显示自定义颜色”，必须同时满足：

1. 嵌入字体并启用 iBooks 字体开关（让“原始字体”模式下样式生效）；
2. 使用苹果官方的夜间模式专用类名，或采用不含该类名的替代方案；
3. 用媒体查询分别定义日间和夜间的颜色。

---

## 二、嵌入字体

### 2.1 准备字体文件

以思源黑体为例（SIL Open Font License 1.1，允许嵌入和分发）：

- 下载 `SourceHanSans-Regular.otf` 和 `SourceHanSans-Bold.otf`
- 放入 EPUB 项目目录，例如 `EPUB/fonts/`

### 2.2 在 CSS 中声明字体

在已有的主样式表（如 `stylesheet1.css`）**最顶部**写入：

```css
@font-face {
    font-family: "SourceHanSans";
    src: url("../fonts/SourceHanSans-Regular.otf");
    font-weight: normal;
    font-style: normal;
}

@font-face {
    font-family: "SourceHanSans";
    src: url("../fonts/SourceHanSans-Bold.otf");
    font-weight: bold;
    font-style: normal;
}
```

注意：`url()` 路径是**相对于 CSS 文件本身**的，不是相对于 HTML 文件。

### 2.3 在 OPF 清单中登记

在 `content.opf` 的 `<manifest>` 末尾添加：

```xml
<item id="font-regular" href="fonts/SourceHanSans-Regular.otf" media-type="application/vnd.ms-opentype"/>
<item id="font-bold" href="fonts/SourceHanSans-Bold.otf" media-type="application/vnd.ms-opentype"/>
```

### 2.4 应用字体

```css
body {
    font-family: "SourceHanSans", sans-serif;
}
```

### 2.5 iBooks 专属开关（可选，视环境而定）

部分环境下需要此文件才能让嵌入字体在“原始字体”模式下生效：

- 路径：`META-INF/com.apple.ibooks.display-options.xml`
- 内容：

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<display_options>
  <platform name="*">
    <option name="specified-fonts">true</option>
  </platform>
</display_options>
```

如果字体已正常显示，可不必手动创建。

---

## 三、自定义文本颜色（含夜间模式）

这一部分有两种实现思路，**互斥**，根据你的需求二选一：

- **方案 A（容器级）**：使用 `ibooks-dark-theme-use-custom-text-color` 类名，接管容器内**所有**文字的颜色。
- **方案 B（局部级）**：不加该类名，只对特定元素（如 `<span>`）单独指定颜色，让普通文本继续由 iBooks 自动决定。

### 方案 A：容器级（接管整个容器）

#### A.1 核心机制

- 给需要自定义颜色的**父容器**加上类名 `ibooks-dark-theme-use-custom-text-color`，iBooks 就不会在夜间模式下覆盖该容器内的颜色。
- 再配合 `@media (prefers-color-scheme: dark)` 和 `@media (prefers-color-scheme: light)`，分别定义日间和夜间的颜色值。

**重要限制：这是“容器级”开关，无法只保护容器内的某一部分文字。** 一旦容器带上了这个类名，容器内**所有**文字的颜色都进入“自定义模式”，Apple Books 不再自动决定其中任何文字的颜色。你必须为容器内的普通文本也显式指定颜色。

#### A.2 推荐的 HTML 结构

```html
<div class="ibooks-dark-theme-use-custom-text-color">
    <p>这是普通文本，<span class="highlight">这是高亮文本</span>。</p>
</div>
```

#### A.3 对应的 CSS 写法

```css
:root {
    color-scheme: light dark;
}

/* 日间模式 */
@media (prefers-color-scheme: light) {
    .ibooks-dark-theme-use-custom-text-color p {
        color: #333333; /* 普通文本在白天的颜色 */
    }
    .ibooks-dark-theme-use-custom-text-color p .highlight {
        color: #cc0000; /* span 在白天的颜色 */
    }
}

/* 夜间模式 */
@media (prefers-color-scheme: dark) {
    .ibooks-dark-theme-use-custom-text-color p {
        color: #e0e0e0; /* 普通文本在夜间的颜色 */
    }
    .ibooks-dark-theme-use-custom-text-color p .highlight {
        color: #ffcc00; /* span 在夜间的颜色 */
    }
}
```


---

### 方案 B：局部级（只改特定元素，推荐）

#### B.1 核心机制

- **不加** `ibooks-dark-theme-use-custom-text-color` 类名。
- 只对需要变色的元素（如 `<span class="highlight">`）单独写 CSS。
- iBooks 仍会自动接管容器内普通文本的颜色（夜间变白），你的 `.highlight` 则在日间/夜间分别显示不同颜色。

**重要前提：方案 B 的夜间自定义颜色，只在“iBooks 夜间模式触发标准 `prefers-color-scheme: dark`”的前提下才生效。** 但根据 5.6 的实测结论，iBooks 的夜间模式**不触发**标准的 `prefers-color-scheme: dark`，而是直接对页面做强制覆盖。所以：

- **`@media (prefers-color-scheme: light)` 生效**，日间颜色正常。
- **`@media (prefers-color-scheme: dark)` 不生效**，夜间 `.highlight` 会被 iBooks 强制变白，你的自定义夜间颜色**显示不出来**。
- 如果你不写夜间规则，`.highlight` 在夜间同样会被强制变白，和普通正文一样。

换句话说，**方案 B 实际上是“只改日间颜色，夜间跟随 iBooks 自动处理”的方案**。

#### B.2 推荐的 HTML 结构

```html
<div>
    <p>这是普通文本，<span class="highlight">这是高亮文本</span>。</p>
</div>
```

#### B.3 对应的 CSS 写法

**写法一（推荐，只写日间颜色）：**

```css
:root {
    color-scheme: light dark;
}

/* 日间模式：自定义颜色 */
@media (prefers-color-scheme: light) {
    .highlight {
        color: #BB5CFF;
    }
}
```

夜间不写规则，`.highlight` 跟随 iBooks 一起变白。

**写法二（写了夜间规则，但在 iBooks 里不生效）：**

```css
:root {
    color-scheme: light dark;
}

@media (prefers-color-scheme: light) {
    .highlight {
        color: #BB5CFF;
    }
}

@media (prefers-color-scheme: dark) {
    .highlight {
        color: red;   /* 在 iBooks 夜间模式下不会生效 */
    }
}
```

这条 `color: red;` 在支持标准 `prefers-color-scheme` 的阅读器（如某些浏览器、Calibre 阅读器）里会生效，但在 iBooks 里不会。

#### B.4 方案 B 的优势

- **普通文本颜色完全由 iBooks 决定**，夜间自动变白、日间自动变黑，无需手动维护。
- **只有指定元素被自定义颜色**，不影响正文。
- **避免了方案 A 中“整个容器被接管”带来的副作用**。
- **实现简单，不易出错。**

#### B.5 方案 B 的局限

- **夜间模式下 `.highlight` 无法保持自定义颜色**，会被 iBooks 强制变白。
- 这是 Apple Books 的机制限制，不是代码能绕过的。
- 如果你一定需要夜间 `.highlight` 保持自定义颜色，只能改用方案 A，接管整个容器。

#### B.6 注意事项

- `:root { color-scheme: light dark; }` 仍然必须写，否则 `prefers-color-scheme` 媒体查询可能不触发。
- 选择器建议用 `.highlight` 而不是 `.类名 p .highlight`。后者在某些 iBooks 版本中会“管得太宽”，导致正文继承 `.highlight` 的颜色（详见第四节 4.5）。
- **不要误以为写了 `@media (prefers-color-scheme: dark)` 就能在 iBooks 夜间模式生效**，这是最常见的误解，详见 5.6。

---

## 方案对比

| 需求 | 推荐方案 | 夜间 `.highlight` 能否自定义 |
|------|---------|------------------------------|
| 只想让某几个词/句变色，正文交给 iBooks | **方案 B** | ❌ 不能（会被强制变白） |
| 想让整段、整章都使用自定义配色，并接管全部文本颜色 | 方案 A | ✅ 能 |
| 追求最小副作用、最稳兼容性 | **方案 B** | —— |
| 夜间也要 `.highlight` 保持自定义颜色 | 只能方案 A | ✅ 能（代价是正文颜色不再自动切换） |

---

## 四、选择器写法速查

以下是本节所有涉及的 CSS 选择器，按“作用范围”从窄到宽排列，并标注适用场景与风险。

### 4.1 通用选择器（不依赖特殊类名）

| 选择器 | 含义 | 适用场景 | 风险 |
|--------|------|---------|------|
| `.highlight` | 选中所有带 `highlight` 类的元素 | 方案 B：只给 `.highlight` 单独写颜色 | 无 |
| `p .highlight` | 选中 `<p>` 内的 `.highlight` | 只想作用于段落里的高亮 | 无 |
| `p.highlight` | 选中**同时是 `<p>` 且带 `highlight` 类**的元素 | 类名直接加在 `<p>` 上 | 注意中间无空格，与上一行含义完全不同 |
| `.highlight, .note` | 同时选中两种类 | 多个类共用一套颜色 | 无 |

### 4.2 容器级选择器（依赖 `ibooks-dark-theme-use-custom-text-color`）

| 选择器 | 含义 | 适用场景 | 风险 |
|--------|------|---------|------|
| `.类名 .highlight` | 类名元素内**任意层级**的 `.highlight` | 方案 A：推荐写法 | 低 |
| `.类名 p .highlight` | 类名元素内的 `<p>` 内的 `.highlight` | 方案 A：结构明确时 | **中**，部分 iBooks 版本会“管得太宽”，导致正文继承 `.highlight` 的颜色（见 5.5） |
| `.类名 p` | 类名元素内的所有 `<p>` | 方案 A：给普通文本显式指定颜色 | 低，但必须写，否则正文无颜色 |
| `.类名 > p` | 类名元素的**直接子元素** `<p>` | 只作用于直接子级，不穿透嵌套 | 低 |
| `.类名 p > .highlight` | 类名元素内 `<p>` 的**直接子元素** `.highlight` | 限定层级，避免误伤嵌套 | 低 |
| `.类名 *` | 类名元素内**所有**元素 | 强制所有元素继承颜色 | 高，可能覆盖标题、引用等 |

### 4.3 选择器书写三条原则

1. **能用 `.highlight` 就不用 `.类名 p .highlight`**：后者越复杂，越容易触发 iBooks 的“容器接管”副作用。
2. **空格代表后代，`>` 代表直接子级，无空格代表同一元素**：三者含义完全不同，写错一个符号结果就变了。
3. **方案 A 必须给普通 `<p>` 也写颜色**：否则正文会继承 `.highlight` 的颜色，出现“整章变红/变蓝”的问题。

### 4.4 快速对照表

| 你想选中什么 | 推荐选择器 |
|-------------|-----------|
| 所有 `.highlight`，无论在哪 | `.highlight` |
| 只选 `<p>` 里的 `.highlight` | `p .highlight` |
| 类名容器内的 `.highlight`（方案 A） | `.类名 .highlight` |
| 类名容器内的普通段落（方案 A） | `.类名 p` |
| 类名容器内 `<p>` 的直接子 `.highlight` | `.类名 p > .highlight` |
| 类名直接加在 `<p>` 上时的该段落 | `.类名`（**不能**写 `.类名 p`） |

### 4.5 实测差异：`.类名 p .highlight` vs `.类名 .highlight`

**测试结论：** 在相同 HTML 结构（`div.类名 > p > span.highlight`）下：

| 写法 | 日间 | 夜间 | 正文颜色 |
|------|------|------|---------|
| `.类名 p .highlight` | span 正确 | span 正确 | **正文被染红/染蓝**（异常） |
| `.类名 .highlight` | span 正确 | span 正确 | 正文保持正常 |

**原因分析：** `.类名 p .highlight` 是一个复合选择器，在某些 iBooks 版本中可能被理解为更强的“容器级自定义样式”信号，导致 iBooks 放弃对容器内其他文字的默认颜色控制，从而让它们继承了 `.highlight` 的颜色。而 `.类名 .highlight` 更简洁，不会触发这种副作用。

**建议：** 如果要走方案 A，选择器尽量简洁，或者干脆改用方案 B（不依赖该类名，只对 `.highlight` 单独写样式）。

---

## 五、常见误解与测试结论

### 5.1 类名能否写进行内样式（`style` 属性）？

**不能。** `class` 和 `style` 是 HTML 元素上两个不同用途的属性：

- `class="ibooks-dark-theme-use-custom-text-color"` 是有效的。
- `style="class: ..."` 是无效的，`style` 属性只接受 CSS 声明（如 `color: red;`）。

行内样式可以写颜色值本身（如 `style="color: #333333;"`），但**同样会被 iBooks 夜间模式覆盖**，因为缺少那个类名。

### 5.2 类名能否只加在 `<span>` 上？

**不行。** 类名的生效逻辑是“**容器内的子元素会继承指定的颜色**”。

- 加在 `<span>` 上：`<span>` 本身不是容器，没有子元素可以继承，夜间模式下颜色依然会被 Apple Books 强制覆盖为白色。
- 加在父容器（`<div>` 或 `<p>`）上：容器内的所有子元素（包括 `<span>`）都会继承你指定的颜色。

### 5.3 能否让普通文本由 iBooks 决定、只让 `<span>` 自定义？

**方案 A 做不到，方案 B 可以。** 这是 Apple Books 机制上的二选一：

- 容器**不带**类名 → 夜间模式下，容器内**所有**文字（包括 `<span>`）都被强制变白，但如果你单独给 `.highlight` 写了夜间颜色，它会生效（**方案 B**）。
- 容器**带上**类名 → 夜间模式下，容器内**所有**文字的颜色都由你的 CSS 控制，普通文本不再由 iBooks 自动决定（**方案 A**）。

### 5.4 只给 `<span>` 加类名的测试结果

**测试结论：正确。** 只给 `<span>` 加 `ibooks-dark-theme-use-custom-text-color` 类名并自定义颜色时：

- **日间模式**：颜色正常显示。
- **夜间模式**：Apple Books 强制使用白色文字，`<span>` 的自定义颜色**失效**。

**原因**：该类名是容器级开关。Apple 官方文档明确说明：“If you do not specify `class="ibooks-dark-theme-use-custom-text-color"`, Apple Books uses white text when a reader selects a dark theme.” 但“specify”指的是在**容器**上指定——只有容器内的**子元素**才会继承颜色。`<span>` 自身没有子元素，因此不满足继承条件。

### 5.5 为什么同一套 CSS 在两本书里效果不同？

**测试结论：** 即使 CSS 写法完全相同，如果两本书的 **HTML 结构不同**，效果也可能完全不同。

- **结构简单、类名作用范围小**：红色只影响 `.highlight`，不会扩散到正文。
- **结构复杂、类名加在最外层大容器上**：一旦容器带上了 `ibooks-dark-theme-use-custom-text-color`，容器内**所有**文字都进入“自定义模式”；如果此时只给 `.highlight` 写了颜色、没给普通 `<p>` 写颜色，普通文本就会**继承**到 `.highlight` 的红色，表现为“整章正文全红”。

**排查方法：**
1. 打开对应章节的 HTML，确认 `ibooks-dark-theme-use-custom-text-color` 加在哪个标签上。
2. 如果是加在 `<div>`、`<section>` 或 `<body>` 这类大容器上，且容器内普通 `<p>` 没有显式颜色，就是这个问题。
3. 解决方式：要么把类名收小到局部容器，要么在 CSS 里给普通 `<p>` 也补上颜色（见 4.3 原则 3）。

### 5.6 iBooks 夜间模式**不触发** `prefers-color-scheme: dark`（关键结论）

**测试背景：** 在 iBooks 里写了下面这段最小化测试：

```css
:root {
    color-scheme: light dark;
}

.highlight {
    color: green !important;
    background-color: yellow !important;
}
```

不带媒体查询，直接给 `.highlight` 上颜色和背景，并加 `!important`。

**测试结果：**

- **日间模式**：`.highlight` 显示绿字黄底，正常。
- **夜间模式**：`.highlight` 既没有绿字，也没有黄底，**什么都没有**。

**结论：** iBooks 的夜间模式**不是通过标准的 `prefers-color-scheme: dark` 媒体查询来通知页面的**，而是**直接对整个页面做了强制覆盖**——在渲染层把文字和背景按它自己的深色方案重绘。

由此可以推出三个重要事实：

1. **`@media (prefers-color-scheme: dark)` 在 iBooks 夜间模式下可能根本不执行**。你写的夜间规则永远等不到触发时机。
2. **`!important` 也无效**。因为它覆盖的是渲染结果，不是 CSS 优先级。
3. **背景色、文字色、边框色等一切颜色声明，在夜间模式下都会被抹掉**，除非容器带有 `ibooks-dark-theme-use-custom-text-color` 类名。

**这意味着：**

- 想让 `.highlight` 在**日间**显示自定义颜色，`@media (prefers-color-scheme: light)` 或直接写规则都可行。
- 想让 `.highlight` 在**夜间**也显示自定义颜色，**不能依赖 `@media (prefers-color-scheme: dark)`**，必须给它的父容器加 `ibooks-dark-theme-use-custom-text-color` 类名，让 iBooks 停止覆盖。
- 一旦加了类名，容器内**所有**文字都进入自定义模式，普通文本也必须显式给颜色，否则会继承 `.highlight` 的颜色。

**最终取舍（无法两全）：**

| 目标 | 能否实现 | 代价 |
|------|---------|------|
| 普通文本由 iBooks 自动控制 + `.highlight` 夜间自定义 | **做不到** | —— |
| 普通文本交给 iBooks + `.highlight` 夜间变白（跟随正文） | 可以 | `.highlight` 夜间失去自定义颜色 |
| 接管整个容器 + `.highlight` 夜间保持自定义颜色 | 可以 | 普通文本颜色日夜都由你指定，不再自动切换 |

这是 Apple Books 机制上的二选一，没有中间状态。


### 5.7 iBooks 对“标题后首段”的特殊处理

测试发现，当 `ibooks-dark-theme-use-custom-text-color` 容器内的第一个 `<p>` 紧跟在 `<h1>`、`<h2>`、`<hr>` 等块级元素之后时，夜间模式下该段落的颜色可能无法写入，其他段落正常。

**原因**：iBooks 对“标题后首段”有独立的内部渲染逻辑，与容器接管机制冲突。

解决方案：在标题与容器之间插入一个空段落 `<p></p>`（可配合不可见样式），让原首段变为第二段，即可绕过此问题。


---

## 六、生效前提与注意事项

1. **读者必须选择“原始字体”**：否则所有自定义颜色（包括夜间模式）都会被覆盖。
2. **对比度要求**：自定义颜色需与背景保持足够对比度，否则可能被系统判定为不可读而强制覆盖。
3. **`:root { color-scheme: light dark; }` 必须写**：否则 `prefers-color-scheme` 媒体查询可能不触发。
4. **类名拼写**：`ibooks-dark-theme-use-custom-text-color` 较长，务必确认拼写正确。
5. **路径一致性**：CSS 中的 `url()` 路径、OPF 中的 `href` 路径、实际文件位置三者必须一致（含大小写）。
6. **字体授权**：嵌入字体需确认授权允许分发。思源黑体为 SIL OFL 1.1，可放心使用；苹方等商业字体不可嵌入分发。
7. **颜色值必须带 `#`**：十六进制颜色如 `#BB5CFF`，漏掉 `#` 会被当作无效值整条丢弃，表现为“颜色不生效”。CSS 内置关键字（如 `red`、`blue`）不需要 `#`。
8. **CSS 规则顺序**：日间规则写在夜间规则**前面**，避免同优先级下后者覆盖前者。
9. **iBooks 夜间模式不触发 `prefers-color-scheme: dark`**：详见 5.6，这是 Apple Books 的渲染机制，不是代码问题。

---

## 七、排查清单

如果字体或颜色不生效，按顺序检查：

- [ ] 读者是否选择了“原始字体”
- [ ] CSS 中 `@font-face` 的 `url()` 路径是否正确
- [ ] OPF 中是否登记了字体文件
- [ ] 字体文件名与路径大小写是否一致
- [ ] 是否写了 `:root { color-scheme: light dark; }`
- [ ] 颜色值是否带了 `#`（十六进制）
- [ ] 日间规则是否写在夜间规则**前面**
- [ ] 是否误用 `@media (prefers-color-scheme: dark)` 期望 iBooks 夜间模式生效（详见 5.6，做不到）
- [ ] 如果走方案 A：是否正确给**父容器**添加了 `ibooks-dark-theme-use-custom-text-color` 类名
- [ ] 如果走方案 A：是否为容器内的普通文本也显式指定了颜色
- [ ] 如果走方案 B：是否**没有**给容器加特殊类名，只对 `.highlight` 单独写样式
- [ ] 选择器是否尽量简洁（避免 `.类名 p .highlight` 这类复合写法带来的副作用）
- [ ] 类名是否误写在 `<span>` 或行内 `style` 属性上
- [ ] 颜色对比度是否足够
- [ ] 重新打包 EPUB 后是否生效