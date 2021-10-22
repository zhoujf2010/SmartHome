<template>
  <div class="ep-entity-item">
    <el-select class="ep-entity-item-select" v-model="entity.entity" placeholder="请选择">
      <el-option v-for="item in types" :key="item.id" :label="item.text" :value="item.id"> </el-option>
    </el-select>
    <div class="ep-entity-item-input-w">
      <el-input class="ep-entity-item-input" :value="entity.value" type="text" readonly></el-input>
    </div>
    <el-button class="ep-entity-item-remove" plain icon="el-icon-delete" title="删除" @click="handleRemove"></el-button>
  </div>
</template>

<script>
import { Button, Select, Option, Input } from 'element-ui';
export default {
  name: 'entity-item',
  components: {
    'el-button': Button,
    'el-select': Select,
    'el-option': Option,
    'el-input': Input
  },
  props: {
    entity: {
      type: Object,
      default: () => {
        return {};
      }
    },
    types: {
      type: Array,
      default: () => []
    }
  },
  computed: {
    detail() {
      return JSON.stringify(this.entity);
    }
  },
  methods: {
    handleRemove() {
      this.$emit('remove-entity');
    }
  }
};
</script>

<style lang="scss">
.ep-entity-item {
  margin-bottom: 10px;
  position: relative;
  &-select {
    width: 120px;
    margin-right: 10px;
    vertical-align: top;
  }
  &-input-w {
    position: absolute;
    top: 0;
    left: 130px;
    right: 66px;
  }
  &-input {
    width: 100%;
    vertical-align: top;
  }
  &-remove {
    position: absolute;
    right: 0;
    padding-top: 0;
    padding-bottom: 0;
    height: 28px;
    line-height: 26px;
    vertical-align: top;
  }
}
</style>
