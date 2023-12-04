package item

type GgpkBaseItemType struct {
	HASH32         int
	Name           string
	ItemClassesKey int
}

type BaseItemType struct {
	En         string
	Zh         string
	GgpkType   *GgpkBaseItemType
	ZhGgpkType *GgpkBaseItemType
}
